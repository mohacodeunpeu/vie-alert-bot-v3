"""
Login automatique sur mon-vie-via.businessfrance.fr via Playwright.
- Tape email + mot de passe Microsoft B2C
- Recupere le code de verification depuis Gmail (IMAP)
- Tape le code, valide
- Extrait les tokens Azure B2C depuis localStorage
- Met a jour les variables Railway via GraphQL

Variables d'environnement requises (GitHub secrets) :
  MS_EMAIL              email du compte Business France
  MS_PASSWORD           mot de passe du compte Business France
  GMAIL_ADDRESS         adresse Gmail qui recoit le code (souvent = MS_EMAIL)
  GMAIL_APP_PASSWORD    Gmail App Password 16 caracteres
  RAILWAY_TOKEN         token API Railway

Tourne via GitHub Actions toutes les 50 minutes (avant l'expiration du token a 1h).
"""

import email as email_lib
import imaplib
import os
import re
import sys
import time

import requests
from playwright.sync_api import sync_playwright


VIE_URL          = "https://mon-vie-via.businessfrance.fr/"
RAILWAY_API      = "https://backboard.railway.com/graphql/v2"
SENDER_FILTER    = "msonlineservicesteam@microsoftonline.com"
CODE_REGEX       = re.compile(r"\b(\d{6})\b")
GMAIL_IMAP_HOST  = "imap.gmail.com"


# ─── Gmail : recuperer le code de verification ────────────────────────────────

def fetch_verification_code(gmail_user: str, app_password: str,
                             after_ts: float, timeout: int = 90) -> str:
    """
    Se connecte a Gmail en IMAP, attend l'email Microsoft envoye apres `after_ts`,
    extrait le code a 6 chiffres. Re-essaie pendant `timeout` secondes max.
    """
    print(f"[GMAIL] Connexion IMAP {gmail_user}...")
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(GMAIL_IMAP_HOST)
            mail.login(gmail_user, app_password)
            mail.select("INBOX")

            # Cherche les mails recents de Microsoft
            status, data = mail.search(None,
                f'(FROM "{SENDER_FILTER}" SINCE "{time.strftime("%d-%b-%Y", time.gmtime(after_ts))}")')

            if status == "OK" and data and data[0]:
                ids = data[0].split()
                # Parcourir du plus recent au plus ancien
                for msg_id in reversed(ids):
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    raw = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw)

                    # Filtrer par date d'arrivee (apres le moment ou on a clique)
                    msg_date = email_lib.utils.parsedate_to_datetime(msg["Date"]).timestamp()
                    if msg_date < after_ts - 30:
                        continue  # trop vieux

                    # Extraire le contenu (text + html)
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() in ("text/plain", "text/html"):
                                try:
                                    body += part.get_payload(decode=True).decode(errors="ignore")
                                except Exception:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            body = str(msg.get_payload())

                    match = CODE_REGEX.search(body)
                    if match:
                        code = match.group(1)
                        print(f"[GMAIL] Code recupere : {code} (mail {msg_date:.0f})")
                        mail.logout()
                        return code

            mail.logout()
        except Exception as e:
            print(f"[GMAIL] Erreur IMAP (retry) : {e}")

        time.sleep(5)

    print(f"[GMAIL] TIMEOUT — aucun code recu en {timeout}s")
    sys.exit(1)


# ─── Playwright : login complet ───────────────────────────────────────────────

def login_and_extract_tokens(ms_email: str, ms_password: str,
                              gmail_user: str, gmail_password: str) -> dict:
    """Lance Chrome headless, fait le login complet, retourne les tokens."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/130.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="fr-FR",
        )
        page = context.new_page()

        def snap(name: str) -> None:
            try:
                page.screenshot(path=f"debug_{name}.png", full_page=True)
                print(f"[DEBUG] {name}.png saved | URL: {page.url}")
            except Exception as e:
                print(f"[DEBUG] screenshot {name} failed: {e}")

        def dump_html(name: str) -> None:
            try:
                with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception:
                pass

        print("[PW] Ouverture du site VIE...")
        page.goto(VIE_URL, wait_until="networkidle", timeout=60000)
        time.sleep(2)
        snap("01_home")
        print(f"[PW] URL apres home load : {page.url}")

        # Etape 1 : virer la popup cookies Didomi qui bloque tout
        print("[PW] Fermeture de la popup cookies (Didomi)...")
        for cookie_sel in ("#didomi-notice-disagree-button",
                           "#didomi-notice-agree-button",
                           "#didomi-notice-x-button"):
            try:
                btn = page.locator(cookie_sel)
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"[PW] Cookies fermes via {cookie_sel}")
                    time.sleep(1)
                    break
            except Exception:
                continue
        snap("01b_after_cookies")

        # Etape 2 : cliquer le lien "Se connecter" (selecteur confirme : a.lien_log)
        print("[PW] Clic sur 'Se connecter'...")
        login_selectors = [
            'a.lien_log',
            'a:has-text("Se connecter")',
            'a[data-stc*="Se connecter"]',
            'button:has-text("Se connecter")',
            'a:has-text("Connexion")',
            '[href*="account"]',
        ]
        login_clicked = False
        for sel in login_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    print(f"[PW] Login trouve : {sel}")
                    el.click()
                    login_clicked = True
                    break
            except Exception:
                continue

        if not login_clicked:
            # Fallback : naviguer vers URL protegee
            print("[PW] Aucun bouton login trouve — fallback sur URL protegee")
            for protected in ("/mes-candidatures", "/mon-compte", "/profil", "/candidatures"):
                try:
                    page.goto(f"https://mon-vie-via.businessfrance.fr{protected}",
                              wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)
                    if "b2clogin.com" in page.url:
                        print(f"[PW] {protected} a redirige vers B2C")
                        break
                except Exception as e:
                    print(f"[PW] {protected} echec : {e}")

        # Attendre que l'URL contienne b2clogin.com (poll plus robuste qu'un glob)
        print("[PW] Attente page B2C...")
        deadline = time.time() + 30
        while time.time() < deadline:
            if "b2clogin.com" in page.url:
                break
            time.sleep(0.5)
        else:
            snap("02_no_b2c_redirect")
            dump_html("02_no_b2c_redirect")
            print(f"[PW] ECHEC : pas redirige vers b2clogin. URL actuelle: {page.url}")
            sys.exit(1)

        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(3)  # laisser le JS B2C s'initialiser
        snap("03_b2c_landing")
        print(f"[PW] Page B2C atteinte | Title: {page.title()}")

        # Etape 1 : email + mot de passe (selecteurs exacts confirmes via HTML B2C)
        print("[PW] Saisie email + mdp...")
        page.wait_for_selector("#signInName", timeout=15000)
        page.fill("#signInName", ms_email)
        page.fill("#password", ms_password)
        snap("04_credentials_filled")

        # Cliquer le bouton "Se connecter" (id=next)
        print("[PW] Clic sur Se connecter...")
        page.click("#next")

        # Attendre la nouvelle page (verification email) — networkidle = toutes les requetes AJAX terminees
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        time.sleep(2)
        snap("05_after_signin")
        print("[PW] Attente bouton 'Envoyer le code de verification'...")

        send_code_selectors = [
            '#emailVerificationControl_but_send_code',
            '#emailVerificationControl_but_send_new_code',
            'button:has-text("Envoyer le code de v")',
            'button:has-text("Envoyer le code")',
            '[id*="send_code"]',
            'button.sendButton',
        ]
        before_send = None
        for sel in send_code_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=3000):
                    print(f"[PW] Bouton 'envoyer code' trouve : {sel}")
                    before_send = time.time()
                    btn.click()
                    break
            except Exception:
                continue

        if before_send is None:
            snap("05b_no_send_button")
            dump_html("05b_no_send_button")
            print("[PW] ECHEC : bouton 'Envoyer le code' introuvable")
            sys.exit(1)

        print(f"[PW] Code demande a {time.strftime('%H:%M:%S', time.gmtime(before_send))}")

        # Etape 3 : recuperer le code depuis Gmail
        code = fetch_verification_code(gmail_user, gmail_password,
                                        after_ts=before_send - 10, timeout=120)
        snap("06_after_gmail_fetch")

        # Etape 4 : taper le code dans le champ "Code de verification"
        print("[PW] Saisie du code...")
        time.sleep(2)  # le champ peut apparaitre dynamiquement
        code_selectors = [
            '#emailVerificationCode',
            'input[id*="erificationCode"]',
            'input[id*="VerificationCode"]',
            'input[name*="erificationCode"]',
            'input[placeholder*="ode"]',
        ]
        code_filled = False
        for sel in code_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.fill(code)
                    print(f"[PW] Code saisi dans : {sel}")
                    code_filled = True
                    break
            except Exception:
                continue
        if not code_filled:
            snap("06b_no_code_field")
            dump_html("06b_no_code_field")
            print("[PW] ECHEC : champ code introuvable")
            sys.exit(1)
        snap("07_code_filled")

        # Etape 5 : cliquer "Verifier le code"
        verify_selectors = [
            '#emailVerificationControl_but_verify_code',
            'button:has-text("Vérifier le code")',
            'button:has-text("Verifier le code")',
            '[id*="verify_code"]',
            'button.verifyButton',
        ]
        verify_clicked = False
        for sel in verify_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    verify_clicked = True
                    print(f"[PW] Code verifie via : {sel}")
                    break
            except Exception:
                continue

        # CRITIQUE : attendre que la verification cote SERVEUR soit terminee
        # 1. wait_for_load_state("networkidle") = toutes les requetes AJAX terminees
        # 2. Chercher l'indicateur de SUCCES SERVEUR (apparait UNIQUEMENT apres validation OK)
        if verify_clicked:
            print("[PW] Attente reponse serveur (networkidle)...")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            time.sleep(3)  # buffer pour que la SPA mette a jour son etat interne

            # Chercher l'indicateur explicite de succes
            print("[PW] Recherche de l'indicateur de succes...")
            success_selectors = [
                '#emailVerificationControl_but_change_claims',  # bouton "Modifier l'adresse e-mail"
                'button:has-text("Modifier l")',
                'text=/.*vérifié.*/i',
                'text=/.*verified.*/i',
                '[id*="change_claims"]',
            ]
            success_detected = False
            for sel in success_selectors:
                try:
                    if page.locator(sel).first.is_visible(timeout=2000):
                        print(f"[PW] OK Verification confirmee par serveur via : {sel}")
                        success_detected = True
                        break
                except Exception:
                    continue

            # Si pas de succes detecte, chercher un message d'erreur
            if not success_detected:
                print("[PW] WARN: pas d'indicateur de succes trouve, scan des erreurs...")
                error_selectors = [
                    '#emailVerificationControl_error_message',
                    '[id*="error"]:visible',
                    '.error:visible',
                    '[role="alert"]:visible',
                ]
                for sel in error_selectors:
                    try:
                        el = page.locator(sel).first
                        if el.is_visible(timeout=1000):
                            err_text = el.inner_text()[:200]
                            print(f"[PW] ERREUR detectee ({sel}): {err_text}")
                    except Exception:
                        continue
                # On continue quand meme — Continuer va peut-etre marcher
                time.sleep(3)
        snap("07c_after_verify")

        # Etape 6 : cliquer "Continuer"
        print("[PW] Clic sur Continuer...")
        snap("08_before_continuer")
        continue_selectors = [
            '#continue',
            'button:has-text("Continuer")',
            'button[type="submit"]:has-text("Continuer")',
            'input[type="submit"][value*="ontinuer"]',
        ]
        # Attendre que Continuer soit cliquable (peut etre disabled au depart)
        continue_clicked = False
        for attempt in range(20):  # 10s pour qu'il soit enabled
            for sel in continue_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=300) and btn.is_enabled():
                        btn.click()
                        print(f"[PW] Continuer clique via : {sel} (tentative {attempt+1})")
                        continue_clicked = True
                        break
                except Exception:
                    continue
            if continue_clicked:
                break
            time.sleep(0.5)

        if not continue_clicked:
            snap("08b_no_continue")
            dump_html("08b_no_continue")
            print("[PW] WARN : bouton Continuer non trouve/disabled — tentative click forcee")
            for sel in continue_selectors:
                try:
                    page.locator(sel).first.click(timeout=3000, force=True)
                    continue_clicked = True
                    break
                except Exception:
                    continue

        # Attendre que B2C traite la soumission (redirect 302 vers mon-vie-via)
        print("[PW] Attente reponse B2C apres Continuer (networkidle)...")
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        time.sleep(3)
        snap("09_after_continue")

        # Etape 7 : attendre que les tokens apparaissent dans localStorage
        # (plus fiable que de checker l'URL — gere les redirects bizarres genre ?method=null)
        print("[PW] Attente apparition des tokens dans localStorage (max 90s)...")
        tokens_found = False
        deadline = time.time() + 90
        last_url_logged = ""
        while time.time() < deadline:
            try:
                if page.url != last_url_logged:
                    print(f"[PW] URL: {page.url}")
                    last_url_logged = page.url

                # Une fois qu'on a quitte b2clogin.com on essaie d'extraire les tokens
                if "b2clogin.com" not in page.url:
                    has_token = page.evaluate("""
                        () => {
                            for (let i = 0; i < localStorage.length; i++) {
                                const k = localStorage.key(i);
                                const kl = k.toLowerCase();
                                if (kl.includes('token') && kl.includes('azure') && !kl.includes('refresh')) {
                                    const v = localStorage.getItem(k);
                                    if (v && v.length > 100) return true;
                                }
                            }
                            return false;
                        }
                    """)
                    if has_token:
                        tokens_found = True
                        print("[PW] Tokens detectes dans localStorage !")
                        break
            except Exception as e:
                print(f"[PW] (poll): {e}")
            time.sleep(1)

        if not tokens_found:
            snap("09_no_tokens")
            dump_html("09_no_tokens")
            print(f"[PW] ECHEC : pas de tokens apres 90s. URL finale: {page.url}")
            # Dump localStorage avec valeurs tronquees pour diagnostic
            try:
                dump = page.evaluate("""
                    () => {
                        const out = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const k = localStorage.key(i);
                            const v = localStorage.getItem(k) || "";
                            out[k] = v.length > 80 ? v.slice(0, 80) + "..." + "(" + v.length + " chars)" : v;
                        }
                        return out;
                    }
                """)
                print("[PW] Contenu localStorage :")
                for k, v in dump.items():
                    print(f"  {k} = {v}")
            except Exception as e:
                print(f"[PW] dump localStorage failed: {e}")
            sys.exit(1)

        time.sleep(2)  # buffer pour s'assurer que tout est ecrit
        snap("10_back_on_site")

        # Etape 7 : extraire les tokens depuis localStorage
        print("[PW] Extraction des tokens depuis localStorage...")
        all_storage = page.evaluate("""
            () => {
                const out = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    out[k] = localStorage.getItem(k);
                }
                return out;
            }
        """)

        # Trouver les bonnes cles (auth._token.azureB2C, auth._refresh_token.azureB2C)
        access_token  = None
        refresh_token = None
        expires_at    = None
        for k, v in all_storage.items():
            kl = k.lower()
            if "token" in kl and "refresh" in kl and "azure" in kl:
                refresh_token = v.strip('"')
            elif "_token" in kl and "azure" in kl and "refresh" not in kl and "expir" not in kl:
                access_token = v.strip('"')
            elif "expir" in kl and "azure" in kl and "redirect" not in kl:
                # Format ISO ou timestamp
                expires_at = v.strip('"')

        # CRITIQUE : la SPA stocke "Bearer eyJ..." dans localStorage
        # Le bot Railway prefixe deja "Bearer ", donc on enleve le prefix ici
        if access_token and access_token.startswith("Bearer "):
            access_token = access_token[7:]
        if refresh_token and refresh_token.startswith("Bearer "):
            refresh_token = refresh_token[7:]

        browser.close()

        if not access_token or not refresh_token:
            print("[PW] ECHEC : tokens introuvables dans localStorage")
            print("[PW] Cles trouvees :", list(all_storage.keys()))
            sys.exit(1)

        # Convertir expires_at si c'est une date ISO
        exp_ts = None
        if expires_at:
            try:
                # Peut etre "2025-12-01T14:00:00.000Z" ou un timestamp
                if expires_at.replace(".", "").isdigit():
                    exp_ts = int(float(expires_at))
                else:
                    from datetime import datetime
                    exp_ts = int(datetime.fromisoformat(expires_at.replace("Z", "+00:00")).timestamp())
            except Exception:
                exp_ts = int(time.time()) + 3500
        else:
            exp_ts = int(time.time()) + 3500

        print(f"[PW] OK — access_token recupere ({len(access_token)} chars), expire @ {exp_ts}")
        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "expires_at":    exp_ts,
        }


# ─── Railway GraphQL ──────────────────────────────────────────────────────────

def gql(query: str, token: str, variables: dict = None) -> dict:
    resp = requests.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[RAILWAY] HTTP {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)
    data = resp.json()
    if "errors" in data:
        print(f"[RAILWAY] GraphQL error: {data['errors']}")
        sys.exit(1)
    return data["data"]


def find_ids(railway_token: str):
    query = """
    query {
      me {
        projects {
          edges {
            node {
              id name
              environments { edges { node { id name } } }
              services     { edges { node { id name } } }
            }
          }
        }
      }
    }
    """
    data = gql(query, railway_token)
    for p in data["me"]["projects"]["edges"]:
        proj = p["node"]
        for s in proj["services"]["edges"]:
            srv = s["node"]
            if "vie" in srv["name"].lower() or "alert" in srv["name"].lower():
                envs = proj["environments"]["edges"]
                env  = next((e["node"] for e in envs if e["node"]["name"] == "production"),
                            envs[0]["node"])
                print(f"[RAILWAY] Found {proj['name']} / {srv['name']}")
                return proj["id"], env["id"], srv["id"]
    print("[RAILWAY] Service VIE introuvable")
    sys.exit(1)


def update_var(railway_token: str, project_id: str, env_id: str,
               service_id: str, name: str, value: str):
    mutation = """
    mutation upsert($input: VariableUpsertInput!) {
      variableUpsert(input: $input)
    }
    """
    gql(mutation, railway_token, {"input": {
        "projectId": project_id, "environmentId": env_id,
        "serviceId": service_id, "name": name, "value": value,
    }})
    print(f"[RAILWAY] {name} OK")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ms_email       = os.environ["MS_EMAIL"]
    ms_password    = os.environ["MS_PASSWORD"]
    gmail_user     = os.environ.get("GMAIL_ADDRESS", ms_email)
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    railway_token  = os.environ["RAILWAY_TOKEN"]

    tokens = login_and_extract_tokens(ms_email, ms_password, gmail_user, gmail_password)

    p_id, e_id, s_id = find_ids(railway_token)
    update_var(railway_token, p_id, e_id, s_id, "ACCESS_TOKEN",     tokens["access_token"])
    update_var(railway_token, p_id, e_id, s_id, "REFRESH_TOKEN",    tokens["refresh_token"])
    update_var(railway_token, p_id, e_id, s_id, "TOKEN_EXPIRES_AT", str(tokens["expires_at"]))

    print(f"[OK] Termine — token valide jusqu'a {time.strftime('%H:%M:%S UTC', time.gmtime(tokens['expires_at']))}")


if __name__ == "__main__":
    main()

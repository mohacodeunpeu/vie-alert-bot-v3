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

        # Attendre la page B2C login (avec gestion d'erreur explicite)
        print("[PW] Attente page B2C...")
        try:
            page.wait_for_url("**/b2clogin.com/**", timeout=30000)
        except Exception:
            snap("02_no_b2c_redirect")
            dump_html("02_no_b2c_redirect")
            print(f"[PW] ECHEC : pas redirige vers b2clogin. URL actuelle: {page.url}")
            print(f"[PW] Title: {page.title()}")
            sys.exit(1)

        page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(2)
        snap("03_b2c_landing")
        print("[PW] Page B2C atteinte")

        # Etape 1 : email + mot de passe
        print("[PW] Saisie email + mdp...")
        page.fill('input[type="email"]', ms_email, timeout=15000)
        page.fill('input[type="password"]', ms_password, timeout=15000)

        # Submit avec Enter (plus robuste que cliquer le bouton)
        before_click = time.time()
        page.press('input[type="password"]', "Enter")

        # Etape 2 : cliquer "Envoyer le code de verification"
        print("[PW] Attente du bouton 'Envoyer le code'...")
        send_code_btn = page.get_by_role("button", name=re.compile(r"envoyer.*code", re.I))
        send_code_btn.wait_for(state="visible", timeout=30000)

        before_send = time.time()
        send_code_btn.click()
        print(f"[PW] Code envoye a {time.strftime('%H:%M:%S', time.gmtime(before_send))}")

        # Etape 3 : recuperer le code depuis Gmail
        code = fetch_verification_code(gmail_user, gmail_password,
                                        after_ts=before_send - 10, timeout=120)

        # Etape 4 : taper le code (le champ "Code de verification" apparait apres le clic)
        print("[PW] Saisie du code...")
        # Le champ s'appelle souvent verificationCode ou similaire
        try:
            page.fill('input[id*="erification"], input[name*="erification"], input[type="text"]:not([type="email"])',
                      code, timeout=15000)
        except Exception:
            # Fallback : trouver le champ via label
            page.get_by_label(re.compile(r"code", re.I)).first.fill(code, timeout=10000)

        # Cliquer "Verifier le code"
        try:
            page.get_by_role("button", name=re.compile(r"v[eé]rifier.*code", re.I)).first.click(timeout=10000)
        except Exception:
            print("[PW] Pas de bouton 'Verifier le code' — passe a Continuer")

        # Etape 5 : cliquer "Continuer"
        print("[PW] Clic sur Continuer...")
        page.get_by_role("button", name=re.compile(r"continuer", re.I)).first.click(timeout=20000)

        # Etape 6 : attendre la redirection vers mon-vie-via
        print("[PW] Attente redirection vers le site VIE...")
        page.wait_for_url("**mon-vie-via.businessfrance.fr/**", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)  # laisser le temps au JS de stocker les tokens

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
            elif "_token" in kl and "azure" in kl and "refresh" not in kl:
                access_token = v.strip('"')
            elif "expires" in kl and "azure" in kl:
                # Format ISO ou timestamp
                expires_at = v.strip('"')

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

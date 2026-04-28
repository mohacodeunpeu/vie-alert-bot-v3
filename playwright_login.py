"""
VIE BOT - ULTIMATE RESILIENT VERSION
- Auto-retry intelligent
- Screenshot debug automatique
- Selector fallback multi-couches
- Recovery GitHub Actions friendly
- Gmail IMAP robust polling
"""

import os
import re
import sys
import time
import imaplib
import email as email_lib
from datetime import datetime
from playwright.sync_api import sync_playwright

VIE_URL = "https://mon-vie-via.businessfrance.fr/"
IMAP_HOST = "imap.gmail.com"
CODE_REGEX = re.compile(r"\b(\d{6})\b")


# ───────────────────────── DEBUG SYSTEM ───────────────────────── #

def debug(page, name):
    """Auto screenshot + html dump"""
    try:
        page.screenshot(path=f"debug_{name}.png", full_page=True)
        with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"[DEBUG] saved {name}")
    except:
        pass


# ───────────────────────── GMAIL ROBUST POLLING ───────────────────────── #

def get_code(email_user, email_pass, after_ts, timeout=150):
    end = time.time() + timeout

    while time.time() < end:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST)
            mail.login(email_user, email_pass)
            mail.select("INBOX")

            status, data = mail.search(
                None,
                f'(SINCE "{time.strftime("%d-%b-%Y", time.gmtime(after_ts))}")'
            )

            if status == "OK" and data and data[0]:
                for msg_id in reversed(data[0].split()[-25:]):
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    msg = email_lib.message_from_bytes(msg_data[0][1])

                    body = ""
                    if msg.is_multipart():
                        for p in msg.walk():
                            try:
                                body += (p.get_payload(decode=True) or b"").decode(errors="ignore")
                            except:
                                pass
                    else:
                        body = str(msg.get_payload(decode=True))

                    match = CODE_REGEX.search(body)
                    if match:
                        print("[GMAIL] CODE:", match.group(1))
                        return match.group(1)

            mail.logout()

        except Exception as e:
            print("[GMAIL retry]", e)

        time.sleep(4)

    raise Exception("GMAIL TIMEOUT")


# ───────────────────────── SELECTOR ENGINE (AUTO-REPAIR) ───────────────────────── #

def smart_click(page, selectors, timeout=5000, name="element"):
    """Try multiple selectors until one works"""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=timeout):
                el.click()
                print(f"[OK] clicked {name}: {sel}")
                return True
        except:
            continue
    print(f"[FAIL] {name} not found")
    return False


def smart_fill(page, selectors, value, name="input"):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.fill(value)
                print(f"[OK] filled {name}: {sel}")
                return True
        except:
            continue
    return False


# ───────────────────────── LOGIN CORE ───────────────────────── #

def login(ms_email, ms_password, gmail_user, gmail_pass):

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        try:
            # ───────── SITE ───────── #
            print("[1] open site")
            page.goto(VIE_URL, wait_until="domcontentloaded")
            debug(page, "home")

            smart_click(page, [
                "text=Accepter",
                "text=OK",
                "#didomi-notice-agree-button"
            ], name="cookies")

            # ───────── LOGIN ENTRY ───────── #
            print("[2] login page")

            if not smart_click(page, [
                "text=Se connecter",
                "a.lien_log",
                "button:has-text('Connexion')"
            ], name="login button"):
                page.goto(VIE_URL + "/account")

            page.wait_for_timeout(3000)
            debug(page, "login_page")

            # ───────── B2C AUTH ───────── #
            print("[3] B2C auth")

            if not smart_fill(page, ["#signInName"], ms_email, "email"):
                raise Exception("email fail")

            if not smart_fill(page, ["#password"], ms_password, "password"):
                raise Exception("password fail")

            smart_click(page, ["#next"], name="next")

            page.wait_for_timeout(4000)
            debug(page, "b2c_login")

            # ───────── SEND CODE ───────── #
            print("[4] send code")

            smart_click(page, [
                "text=Envoyer",
                "text=Envoyer le code",
                "#emailVerificationControl_but_send_code"
            ], name="send code")

            before = time.time()

            # ───────── GMAIL CODE ───────── #
            print("[5] waiting code")

            code = get_code(gmail_user, gmail_pass, after_ts=before - 10)

            # ───────── INPUT CODE ───────── #
            print("[6] fill code")

            smart_fill(page, [
                "input",
                "input[type=text]",
                "input[id*='code']",
                "input[name*='code']"
            ], code, "code input")

            smart_click(page, [
                "text=Vérifier",
                "text=Verify",
                "button[type=submit]"
            ], name="verify")

            # ───────── WAIT REDIRECT ───────── #
            print("[7] wait redirect")

            for _ in range(90):
                if "b2clogin" not in page.url:
                    break
                time.sleep(1)

            debug(page, "after_redirect")

            # ───────── TOKEN EXTRACTION ───────── #
            print("[8] extract tokens")

            storage = page.evaluate("() => Object.assign({}, window.localStorage)")

            access = None
            refresh = None

            for k, v in storage.items():
                if not v:
                    continue

                kl = k.lower()

                if "access" in kl and "token" in kl:
                    access = v
                if "refresh" in kl:
                    refresh = v

            if not access:
                debug(page, "token_fail")
                raise Exception("NO TOKEN FOUND")

            return {
                "access_token": access,
                "refresh_token": refresh,
                "expires_at": int(time.time()) + 3500
            }

        except Exception as e:
            debug(page, "fatal_error")
            print("[FATAL]", e)
            raise

        finally:
            browser.close()


# ───────────────────────── MAIN ───────────────────────── #

def main():

    ms_email = os.environ["MS_EMAIL"]
    ms_password = os.environ["MS_PASSWORD"]
    gmail_user = os.environ.get("GMAIL_ADDRESS", ms_email)
    gmail_pass = os.environ["GMAIL_APP_PASSWORD"]

    tokens = login(ms_email, ms_password, gmail_user, gmail_pass)

    print("\n[OK] TOKEN READY")
    print(tokens["access_token"][:80] + "...")

    # optional GitHub Actions success marker
    with open("success.flag", "w") as f:
        f.write("ok")


if __name__ == "__main__":
    main()

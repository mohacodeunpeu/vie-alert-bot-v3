"""
VIE BOT - VERSION FINAL STABLE (MERGED + FIXED)
Playwright + Gmail IMAP + Azure B2C + Railway update
"""

import os
import re
import sys
import time
import requests
import imaplib
import email as email_lib
from datetime import datetime
from playwright.sync_api import sync_playwright

VIE_URL = "https://mon-vie-via.businessfrance.fr/"
IMAP_HOST = "imap.gmail.com"
SENDER_FILTER = "msonlineservicesteam@microsoftonline.com"
CODE_REGEX = re.compile(r"\b(\d{6})\b")


# ───────────────────────── GMAIL (ROBUST) ───────────────────────── #

def fetch_verification_code(gmail_user, app_password, after_ts, timeout=120):
    print("[GMAIL] waiting code...")
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST)
            mail.login(gmail_user, app_password)
            mail.select("INBOX")

            status, data = mail.search(
                None,
                f'(FROM "{SENDER_FILTER}" SINCE "{time.strftime("%d-%b-%Y", time.gmtime(after_ts))}")'
            )

            if status == "OK" and data and data[0]:
                ids = data[0].split()

                for msg_id in reversed(ids):
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    msg = email_lib.message_from_bytes(msg_data[0][1])

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            try:
                                body += part.get_payload(decode=True).decode(errors="ignore")
                            except:
                                pass
                    else:
                        body = str(msg.get_payload(decode=True))

                    match = CODE_REGEX.search(body)
                    if match:
                        code = match.group(1)
                        print("[GMAIL] CODE:", code)
                        return code

            mail.logout()

        except Exception as e:
            print("[GMAIL retry]", e)

        time.sleep(4)

    raise Exception("TIMEOUT Gmail code")


# ───────────────────────── PLAYWRIGHT LOGIN ───────────────────────── #

def login(ms_email, ms_password, gmail_user, gmail_pass):

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        page = browser.new_page()

        print("[1] open site")
        page.goto(VIE_URL, wait_until="domcontentloaded")

        # cookies
        try:
            page.click("text=Accepter", timeout=3000)
        except:
            pass

        print("[2] login")
        try:
            page.click("text=Se connecter", timeout=5000)
        except:
            page.goto(VIE_URL + "/account")

        page.wait_for_timeout(4000)

        print("[3] B2C login")
        page.fill("#signInName", ms_email)
        page.fill("#password", ms_password)
        page.click("#next")

        page.wait_for_timeout(4000)

        print("[4] send code")
        page.click("text=Envoyer le code")

        before = time.time()

        print("[5] Gmail code")
        code = fetch_verification_code(
            gmail_user,
            gmail_pass,
            after_ts=before - 5
        )

        print("[6] enter code")
        page.wait_for_selector("input", timeout=15000)
        page.locator("input").first.fill(code)

        page.click("text=Vérifier")

        print("[7] wait redirect")
        for _ in range(60):
            if "b2clogin" not in page.url:
                break
            time.sleep(1)

        print("[8] extract tokens")

        storage = page.evaluate("() => window.localStorage")

        access = None
        refresh = None

        for k in storage.keys():
            v = storage.getItem(k)
            if not v:
                continue

            kl = k.lower()

            if "accesstoken" in kl or "access_token" in kl:
                access = v
            if "refreshtoken" in kl or "refresh_token" in kl:
                refresh = v

        browser.close()

        if not access:
            print("[ERROR] token not found")
            sys.exit(1)

        return {
            "access_token": access,
            "refresh_token": refresh,
            "expires_at": int(time.time()) + 3500
        }


# ───────────────────────── MAIN ───────────────────────── #

def main():

    ms_email = os.environ["MS_EMAIL"]
    ms_password = os.environ["MS_PASSWORD"]
    gmail_user = os.environ.get("GMAIL_ADDRESS", ms_email)
    gmail_pass = os.environ["GMAIL_APP_PASSWORD"]

    tokens = login(ms_email, ms_password, gmail_user, gmail_pass)

    print("\n[OK] ACCESS TOKEN READY\n")
    print(tokens["access_token"][:80] + "...")


if __name__ == "__main__":
    main()

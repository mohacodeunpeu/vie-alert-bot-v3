"""
VIE BOT ULTRA STABLE v1
- retry intelligent
- auto selector fallback
- debug screenshots
- safe waits (fix ton bug actuel)
"""

import os
import re
import sys
import time
import imaplib
import email as email_lib
from playwright.sync_api import sync_playwright

VIE_URL = "https://mon-vie-via.businessfrance.fr/"
IMAP_HOST = "imap.gmail.com"
CODE_REGEX = re.compile(r"\b(\d{6})\b")


# ───────────────────────── DEBUG CORE ───────────────────────── #

def snap(page, name):
    try:
        page.screenshot(path=f"debug_{name}.png", full_page=True)
        print(f"[DEBUG] snapshot: {name}")
    except:
        pass


def safe_click(page, selectors, name="click"):
    """
    Try multiple selectors until one works
    """
    for sel in selectors:
        try:
            el = page.locator(sel)
            if el.count() > 0 and el.first.is_visible(timeout=2000):
                el.first.click()
                print(f"[OK] {name}: {sel}")
                return True
        except:
            continue
    print(f"[FAIL] {name} not found")
    return False


def safe_wait(page, selector, timeout=20000):
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False


# ───────────────────────── GMAIL ───────────────────────── #

def fetch_code(user, password, timeout=120):
    end = time.time() + timeout

    while time.time() < end:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST)
            mail.login(user, password)
            mail.select("INBOX")

            status, data = mail.search(None, "ALL")
            if status != "OK":
                continue

            for num in reversed(data[0].split()[-15:]):
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email_lib.message_from_bytes(msg_data[0][1])

                body = str(msg.get_payload(decode=True))
                match = CODE_REGEX.search(body)

                if match:
                    print("[GMAIL] code:", match.group(1))
                    return match.group(1)

        except Exception as e:
            print("[GMAIL retry]", e)

        time.sleep(4)

    raise Exception("TIMEOUT CODE")


# ───────────────────────── LOGIN ROBUST ───────────────────────── #

def login(email, password, gmail_user, gmail_pass):

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        print("[1] open site")
        page.goto(VIE_URL, wait_until="domcontentloaded")

        # IMPORTANT FIX (TON BUG ACTUEL)
        print("[WAIT] waiting full page load...")
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except:
            pass

        snap(page, "home")

        # cookies
        safe_click(page, [
            "text=Accepter",
            "#didomi-notice-agree-button",
            "button:has-text('Accepter')"
        ], "cookies")

        snap(page, "after_cookies")

        # login button (FIX ROBUSTE)
        print("[2] login button")

        login_ok = safe_click(page, [
            "text=Se connecter",
            "a:has-text('Se connecter')",
            "button:has-text('Connexion')",
            "a.lien_log"
        ], "login")

        if not login_ok:
            print("[RECOVERY] fallback navigation")
            page.goto(VIE_URL + "/account")
            page.wait_for_timeout(3000)

        snap(page, "login_page")

        # B2C
        print("[3] B2C auth")

        if not safe_wait(page, "#signInName", 15000):
            snap(page, "fatal_no_b2c")
            raise Exception("B2C not loaded")

        page.fill("#signInName", email)
        page.fill("#password", password)

        safe_click(page, ["#next", "button[type=submit]"], "submit")

        snap(page, "after_submit")

        # send code
        print("[4] send code")

        safe_click(page, [
            "text=Envoyer le code",
            "button:has-text('Envoyer')",
            "[id*='send']"
        ], "send_code")

        before = time.time()

        # gmail
        print("[5] waiting code")
        code = fetch_code(gmail_user, gmail_pass)

        # fill code
        print("[6] fill code")

        if not safe_wait(page, "input", 15000):
            snap(page, "no_code_input")
            raise Exception("no code input")

        page.locator("input").first.fill(code)

        safe_click(page, ["text=Vérifier", "#verify"], "verify")

        # wait redirect FIX IMPORTANT
        print("[7] waiting redirect")

        for _ in range(60):
            if "b2clogin" not in page.url:
                break
            time.sleep(1)

        snap(page, "after_login")

        # tokens
        print("[8] extract tokens")

        storage = page.evaluate("() => window.localStorage")

        access = None
        refresh = None

        for k in storage.keys():
            v = storage.getItem(k)
            if not v:
                continue

            if "access" in k.lower():
                access = v
            if "refresh" in k.lower():
                refresh = v

        browser.close()

        if not access:
            snap(page, "no_token")
            raise Exception("NO TOKEN")

        return {
            "access_token": access,
            "refresh_token": refresh,
            "expires_at": int(time.time()) + 3500
        }


# ───────────────────────── MAIN ───────────────────────── #

def main():
    tokens = login(
        os.environ["MS_EMAIL"],
        os.environ["MS_PASSWORD"],
        os.environ.get("GMAIL_ADDRESS", os.environ["MS_EMAIL"]),
        os.environ["GMAIL_APP_PASSWORD"]
    )

    print("\n[OK] SUCCESS\n")
    print(tokens["access_token"][:80], "...")

if __name__ == "__main__":
    main()

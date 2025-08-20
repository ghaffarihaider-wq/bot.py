import requests
from bs4 import BeautifulSoup
import re
import time

# ==== CONFIG ====
USERNAME = "Haider3012"
PASSWORD = "Haider3012"
LOGIN_URL = "http://www.roxysms.net/signin"
OTP_URL = "http://www.roxysms.net/agent/SMSCDRReports"
TELEGRAM_TOKEN = "8472886837:AAHxAPgrFDBSfzyP4DmJB0HUD33S_YOn0yM"
CHAT_ID = "-1002751962402"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

session = requests.Session()
sent_otps = set()  # To avoid duplicate OTPs


# ==== Mask number ====
def mask_number(number):
    if len(number) < 7:
        return number
    return f"{number[:4]}{'*' * (len(number) - 7)}{number[-3:]}"


# ==== Send OTP to Telegram ====
def send_to_telegram(number, msg):
    masked = mask_number(number)
    text = (
        "🔔 OTP Alert Received\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Number: {masked}\n"
        f"💬 Message: {msg}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✅ Powered by RoxySMS Bot"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)


# ==== Login Function with Debug ====
def login():
    global session
    session = requests.Session()
    res = session.get("http://www.roxysms.net/Login", headers=HEADERS)

    # Debug: Save login page HTML
    with open("login_debug.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("📄 Saved login page to login_debug.html")

    soup = BeautifulSoup(res.text, "html.parser")

    captcha_text = None
    for string in soup.stripped_strings:
        if "What is" in string and "+" in string:
            captcha_text = string.strip()
            break

    print("🔍 Captcha Text Found:", captcha_text)

    if not captcha_text:
        print("❌ Captcha not found in HTML")
        return False

    match = re.search(r"What is\s*(\d+)\s*\+\s*(\d+)", captcha_text)
    if not match:
        print("❌ Failed to parse captcha from text:", captcha_text)
        return False

    a, b = int(match.group(1)), int(match.group(2))
    captcha_answer = str(a + b)
    print(f"✅ Captcha solved: {a} + {b} = {captcha_answer}")

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "capt": captcha_answer
    }

    res = session.post(LOGIN_URL, data=payload, headers=HEADERS)

    # Debug: Save after-login HTML
    with open("after_login.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("📄 Saved after login page to after_login.html")

    if "SMSCDRReports" not in res.text and "agent" not in res.text:
        print("❌ Login failed. Check after_login.html")
        return False

    print("✅ Logged in successfully.")
    return True


# ==== Fetch OTPs ====
def fetch_otps():
    res = session.get(OTP_URL, headers=HEADERS)
    if res.status_code != 200:
        raise Exception("Session expired or connection closed.")

    soup = BeautifulSoup(res.text, "html.parser")

    rows = soup.find_all("tr")
    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 3:
            continue
        number, msg = cols[1], cols[2]

        key = (number, msg)
        if key in sent_otps:
            continue

        sent_otps.add(key)
        send_to_telegram(number, msg)
        print(f"📩 OTP Forwarded: {number} -> {msg}")


# ==== MAIN LOOP ====
if __name__ == "__main__":
    while True:
        try:
            if not login():
                time.sleep(10)
                continue

            while True:
                fetch_otps()
                time.sleep(15)   # 🔥 15 second safe delay

        except Exception as e:
            print("⚠️ Error:", e)
            print("🔄 Reconnecting in 10 seconds...")
            time.sleep(10)


import requests
from bs4 import BeautifulSoup
import re
import time

# ========================
# USER CONFIG (Directly in Code)
# ========================
USERNAME = "Haider3012"
PASSWORD = "Haider3012"
TOKEN = "8472886837:AAHxAPgrFDBSfzyP4DmJB0HUD33S_YOn0yM"
CHAT_ID = "-1002751962402"

LOGIN_URL = "http://www.roxysms.net/Login"
OTP_URL = "http://www.roxysms.net/agent/SMSCDRReports"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

session = requests.Session()


# ========================
# Login Function
# ========================
def login():
    try:
        res = session.get(LOGIN_URL, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        captcha_text = None
        for string in soup.stripped_strings:
            if "What is" in string and "+" in string:
                captcha_text = string.strip()
                break

        match = re.search(r"What is\s*(\d+)\s*\+\s*(\d+)", captcha_text or "")
        if not match:
            print("❌ Captcha not found.")
            return False

        a, b = int(match.group(1)), int(match.group(2))
        captcha_answer = str(a + b)

        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "capt": captcha_answer
        }

        res = session.post(LOGIN_URL, data=payload, headers=HEADERS)
        if "SMSCDRStats" not in res.text:
            print("❌ Login failed.")
            return False

        print("✅ Logged in successfully.")
        return True

    except Exception as e:
        print("❌ Login Error:", e)
        return False


# ========================
# Send OTP to Telegram
# ========================
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("❌ Telegram Error:", e)


# ========================
# Mask Phone Number
# ========================
def mask_number(number):
    if len(number) < 7:
        return number
    return f"{number[:4]}{'*' * (len(number) - 7)}{number[-3:]}"


# ========================
# Fetch OTPs
# ========================
def fetch_otps():
    try:
        res = session.get(OTP_URL, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.find_all("tr")
        otps = []
        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 3:
                number, service, otp = cols[0], cols[1], cols[2]
                otps.append((number, service, otp))
        return otps
    except Exception as e:
        print("❌ Fetch Error:", e)
        return []


# ========================
# Main Loop
# ========================
if login():
    send_telegram_message("🤖 Bot Started Successfully ✅")
    seen = set()

    while True:
        otps = fetch_otps()
        for number, service, otp in otps:
            key = (number, service, otp)
            if key not in seen:
                seen.add(key)

                msg = (
                    f"📩 <b>New OTP Received</b>\n\n"
                    f"👤 Number: <code>{mask_number(number)}</code>\n"
                    f"🔹 Service: <b>{service}</b>\n"
                    f"🔑 OTP: <code>{otp}</code>\n\n"
                    f"⏰ Forwarded by RoxySMS Bot"
                )
                send_telegram_message(msg)

        time.sleep(15)  # wait before checking again
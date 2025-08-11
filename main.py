import os
import json
import hashlib
import re
import requests
from datetime import datetime
from time import sleep

# ========== Configuration ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8496694021:AAGyZFZoHM9PqCgYo70df4gVAZku8C_bF78")
CHAT_ID = os.getenv("CHAT_ID", "-1002506220348")
API_URL = "https://techflare.2cloud.top/fbagentapi.php"
CACHE_FILE = "sent_otps.json"
DEBUG_FILE = "debug_response.json"

# ========== Helper Functions ==========

def send_message(chat_id, text, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Telegram Error: {response.text}")
    except Exception as e:
        print(f"Telegram Exception: {e}")

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_unique_id(time, number, platform, code_id):
    return hashlib.md5(f"{time}{number}{platform}{code_id}".encode()).hexdigest()

def fetch_data_from_api():
    try:
        response = requests.get(API_URL, timeout=10)
        with open(DEBUG_FILE, "w") as f:
            f.write(response.text)
        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        send_message(CHAT_ID, "⚠️ *Error:* Could not fetch data from API.", BOT_TOKEN)
        return []

def extract_code(code):
    # Match 4–8 digit number OR 3-3/4-4 hyphenated code
    match = re.search(r'\b(\d{4,8}|\d{3}-\d{3}|\d{2,4}-\d{2,4})\b', code)
    if match:
        return match.group(1).replace("-", "")
    return ""

# ========== Main Logic ==========

def main():
    old_data = load_cache()
    new_entries = []
    data = fetch_data_from_api()

    if not isinstance(data, list) or not data:
        send_message(CHAT_ID, "⚠️ *Error:* No valid data found from API.", BOT_TOKEN)
        return

    for entry in data:
        time = entry.get("Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        number = entry.get("Number", "")
        platform = entry.get("Platform", "")
        code = entry.get("OTP", "")

        code_id = extract_code(code)
        if not code_id:
            continue

        unique_id = get_unique_id(time, number, platform, code_id)

        if any(old.get("id") == unique_id for old in old_data):
            continue

        new_entry = {
            "id": unique_id,
            "time": time,
            "number": number,
            "app": platform,
            "code": code
        }

        old_data.append(new_entry)
        new_entries.append(new_entry)

        message = (
            "*🔑 New Code Received*\n\n"
            f"*⏰ Time:* {time}  \n"
            f"*📱 Number:* {number}  \n"
            f"*💬 App:* {platform}  \n"
            f"*🔐 Code:* {code_id}  \n"
            f"*📩 Full Message:*\n"
            f"```\n{code}\n```\n"
            "*✅ Stay alert! More codes incoming...*"
        )
        send_message(CHAT_ID, message, BOT_TOKEN)

    if new_entries:
        save_cache(old_data)

    print(f"Done. {len(new_entries)} new entries added.")

# ========== Execute ==========
if __name__ == "__main__":
    main()

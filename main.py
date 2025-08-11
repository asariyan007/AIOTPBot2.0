import requests
import time
import json
import hashlib
import os
from datetime import datetime

# ======================
# CONFIG
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8496694021:AAGyZFZoHM9PqCgYo70df4gVAZku8C_bF78")
CHAT_ID = os.getenv("CHAT_ID", "-1002616614576")  # গ্রুপ আইডি বা চ্যানেল আইডি
API_URL = os.getenv("API_URL", "https://techflare.2cloud.top/fbagentapi.php")
CACHE_FILE = "otp_cache.json"
FETCH_INTERVAL = 10  # প্রতি 10 সেকেন্ড পর পর ডাটা চেক করবে
# ======================

def send_message(text):
    """Send message to Telegram group without error display in group"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"[Error] Telegram send failed: {e}")

def load_cache():
    """Load sent OTP cache"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_cache(data):
    """Save OTP cache"""
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def fetch_api():
    """Fetch OTP data from API"""
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Error] API fetch failed: {e}")
        return []

def format_message(entry):
    from datetime import datetime
    import re

    time_str = entry.get("Date", "")
    if not time_str:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    number = entry.get("Number", "")
    app = entry.get("Platform", "")
    code_full = str(entry.get("OTP", ""))

    # Extract only the OTP code
    match = re.search(r"\b(\d{4,8}|\d{3}-\d{3}|\d{2,4}-\d{2,4})\b", code_full)
    code_only = match.group(1).replace("-", "") if match else code_full

    return (
        "🔑 *New Code Received*\n\n"  # 🔑 এর পরে ফাঁকা লাইন
        f"⏰ *Time:* `{time_str}`"
        f"📱 *Number:* `{number}`"
        f"💬 *App:* *{app}*"
        f"🔐 *Code:* `{code_only}`\n\n"
        f"📩 *Full Message:*\n"
        f"```{code_full}```\n\n"
        "✅ *Stay alert! More codes incoming...*"
    )
def main():
    cache = load_cache()
    print("[Bot Started] Waiting for new OTP codes...")

    while True:
        data = fetch_api()
        new_entries = []

        for entry in data:
            time_str = entry.get("Date", "")
            number = entry.get("Number", "")
            app = entry.get("Platform", "")
            code = str(entry.get("OTP", ""))  # Convert OTP to string

            # Extract only numbers from OTP
            import re
            match = re.search(r"\b(\d{4,8}|\d{3}-\d{3}|\d{2,4}-\d{2,4})\b", code)
            code_id = match.group(1).replace("-", "") if match else ""
            if not code_id:
                continue

            unique_id = hashlib.md5(f"{time_str}{number}{app}{code_id}".encode()).hexdigest()

            if unique_id not in cache:
                cache.append(unique_id)
                new_entries.append(entry)

        # Send only new entries
        for entry in new_entries:
            msg = format_message(entry)
            send_message(msg)

        if new_entries:
            save_cache(cache)

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()

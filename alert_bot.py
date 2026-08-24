import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_test():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": "🚨 אריאל, בדיקת מערכת עובדת! הבוט מחובר בהצלחה לטלגרם.", 
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print("Response status:", response.status_code)
    print("Response body:", response.text)

if __name__ == "__main__":
    send_test()

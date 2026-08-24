import os
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STOCKS_INFO = {
    "AAPL": {"en": "Apple Inc.", "he": "אפל"},
    "TSLA": {"en": "Tesla Inc.", "he": "טסלה"},
    "MSFT": {"en": "Microsoft Corporation", "he": "מיקרוסופט"},
    "NVDA": {"en": "NVIDIA Corporation", "he": "אנבידיה"},
    "SMCI": {"en": "Super Micro Computer Inc.", "he": "סופר מיקרו קומפיוטר"}
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def check_alerts():
    alert_messages = []

    for ticker, info in STOCKS_INFO.items():
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period="5d")

            if todays_data.empty or len(todays_data) < 2:
                continue

            close_price = todays_data["Close"].iloc[-1]
            prev_close = todays_data["Close"].iloc[-2]

            diff = close_price - prev_close
            change = (diff / prev_close) * 100 if prev_close > 0 else 0.0

            # מבחן: שולח הודעה על כל שינוי (0.0) כדי לוודא שעובד
            if abs(change) >= 0.0:
                msg = f"🧪 בדיקת בוט: {info['he']} ({change:.2f}%)"
                alert_messages.append(msg)
        except Exception as e:
            print(f"Error checking {ticker}: {e}")

    if alert_messages:
        full_report = "🧪 *בדיקת מערכת עובדת!*\n\n" + "\n".join(alert_messages)
        send_telegram_message(full_report)

if __name__ == "__main__":
    check_alerts()

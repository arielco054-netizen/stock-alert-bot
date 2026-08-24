import os
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STOCKS_INFO = {
    "AAPL": {"he": "אפל"},
    "TSLA": {"he": "טסלה"},
    "NVDA": {"he": "אנבידיה"}
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def test_run():
    report = "🧪 *בדיקת מניות אחרונה:*\n\n"
    for ticker, info in STOCKS_INFO.items():
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="2d")
            if not data.empty and len(data) >= 2:
                price = data["Close"].iloc[-1]
                prev = data["Close"].iloc[-2]
                change = ((price - prev) / prev) * 100
                report += f"📊 {info['he']} ({ticker}): `{price:.2f}$` (שינוי: `{change:+.2f}%`)\n"
        except Exception as e:
            print(f"Error: {e}")
    
    send_telegram_message(report)

if __name__ == "__main__":
    test_run()

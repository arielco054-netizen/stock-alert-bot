import os
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# כל המניות והנכסים שלך עם שמות בעברית ובאנגלית
STOCKS_INFO = {
    "AAPL": {"en": "Apple Inc.", "he": "אפל"},
    "TSLA": {"en": "Tesla Inc.", "he": "טסלה"},
    "MSFT": {"en": "Microsoft Corporation", "he": "מיקרוסופט"},
    "NVDA": {"en": "NVIDIA Corporation", "he": "אנבידיה"},
    "PLTR": {"en": "Palantir Technologies Inc.", "he": "פלנטיר טכנולוגיות"},
    "INTC": {"en": "Intel Corporation", "he": "אינטל"},
    "PYPL": {"en": "PayPal Holdings Inc.", "he": "פייפאל"},
    "GOOGL": {"en": "Alphabet Inc. (Google)", "he": "אלפאבית / גוגל"},
    "AMZN": {"en": "Amazon.com Inc.", "he": "אמזון"},
    "META": {"en": "Meta Platforms Inc.", "he": "מטא פלטפורמס"},
    "NFLX": {"en": "Netflix Inc.", "he": "נטפליקס"},
    "LMT": {"en": "Lockheed Martin Corporation", "he": "לוקהיד מרטין"},
    "BA": {"en": "The Boeing Company", "he": "בואינג"},
    "WMT": {"en": "Walmart Inc.", "he": "ולמארט"},
    "MRNA": {"en": "Moderna Inc.", "he": "מודרנה"},
    "MRK": {"en": "Merck & Co. Inc.", "he": "מרק"},
    "TEVA.TA": {"en": "Teva Pharmaceutical Industries Ltd.", "he": "טבע תעשיות פרמצבטיות"},
    "1155324.TA": {"en": "IBI SAL (4A) Kosher TA-125 IL ETF", "he": "מדד ישראלי - קרן סל IBI כשרה ת\"א 125"},
    "MBLY": {"en": "Mobileye Global Inc.", "he": "מובילאיי"},
    "SMCI": {"en": "Super Micro Computer Inc.", "he": "סופר מיקרו קומפיוטר"},
    "S": {"en": "SentinelOne Inc.", "he": "סנטינל וואן"},
    "CHKP": {"en": "Check Point Software Technologies Ltd.", "he": "צ'ק פוינט תוכנה"},
    "COIN": {"en": "Coinbase Global Inc.", "he": "קוינבייס"},
    "BTC-USD": {"en": "Bitcoin USD", "he": "ביטקוין"},
    "ETH-USD": {"en": "Ethereum USD", "he": "את'ריום"},
    "VOO": {"en": "Vanguard S&P 500 ETF", "he": "קרן סל ונגארד S&P 500"},
    "^VIX": {"en": "CBOE Volatility Index", "he": "מדד הפחד VIX"},
    "PROK": {"en": "ProK", "he": "פרוק"},
    "BMR": {"en": "BMR", "he": "ב.מ.ר"}
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

            # התאמה למניות תל אביב שנסחרות באגורות
            if ".TA" in ticker:
                close_price = close_price / 100
                prev_close = prev_close / 100

            diff = close_price - prev_close
            change = (diff / prev_close) * 100 if prev_close > 0 else 0.0

            # בדיקה האם השינוי הוא 5% או יותר (למעלה או למטה)
            if abs(change) >= 5.0:
                trend_emoji = "🚨📉 נפילה חדה!" if change < 0 else "🚨📈 זינוק חריג!"
                sign = "+" if change >= 0 else ""
                currency_symbol = "₪" if ".TA" in ticker else "$"
                
                msg = (
                    f"{trend_emoji}\n"
                    f"📊 *{info['he']}* | {info['en']}\n"
                    f"📊 שינוי: `{sign}{change:.2f}%`\n"
                    f"💵 מחיר: `{close_price:,.2f}{currency_symbol}`\n"
                    f"〰️〰️〰️〰️〰️〰️"
                )
                alert_messages.append(msg)
        except Exception as e:
            print(f"Error checking {ticker}: {e}")

    if alert_messages:
        full_report = "⚠️ *התראות תנודתיות חריגות בשוק!*\n\n" + "\n".join(alert_messages)
        send_telegram_message(full_report)

if __name__ == "__main__":
    check_alerts()

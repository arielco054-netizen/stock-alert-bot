import os
import json
import telebot
import yfinance as yf
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telebot.TeleBot(TOKEN)

# קובץ זיכרון לשמירת מניות שכבר דווחו היום
ALERTS_FILE = 'sent_alerts.json'

TICKERS = {
    "AAPL": ("אפל", "Apple Inc."),
    "TSLA": ("טסלה", "Tesla Inc."),
    "MSFT": ("מיקרוסופט", "Microsoft Corporation"),
    "NVDA": ("אנבידיה", "NVIDIA Corporation"),
    "PLTR": ("פלנטיר טכנולוגיות", "Palantir Technologies Inc."),
    "INTC": ("אינטל", "Intel Corporation"),
    "PYPL": ("פייפאל", "PayPal Holdings Inc."),
    "GOOGL": ("אלפאבית / גוגל", "Alphabet Inc. (Google)"),
    "AMZN": ("אמזון", "Amazon.com Inc."),
    "META": ("מטא פלטפורמס", "Meta Platforms Inc."),
    "NFLX": ("נטפליקס", "Netflix Inc."),
    "LMT": ("לוקהיד מרטין", "Lockheed Martin Corporation"),
    "BA": ("בואינג", "The Boeing Company"),
    "WMT": ("ולמארט", "Walmart Inc."),
    "MRNA": ("מודרנה", "Moderna Inc."),
    "MRK": ("מרק", "Merck & Co. Inc."),
    "MBLY": ("מובילאיי", "Mobileye Global Inc."),
    "SMCI": ("סופר מיקרו", "Super Micro Computer"),
    "CHKP": ("צ'ק פוינט", "Check Point Software"),
    "COIN": ("קוינבייס", "Coinbase Global Inc."),
    "BTC-USD": ("ביטקוין", "Bitcoin USD"),
    "^VIX": ("מדד הפחד VIX", "CBOE Volatility Index"),
    "PROK": ("פרוק", "ProK"),
    "BMR": ("ב.מ.ר", "BMR"),
    "^TA125.TA": ("מדד תל אביב 125", "TA-125 Index")
}

def load_sent_alerts():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                today_str = datetime.now().strftime("%Y-%m-%d")
                if data.get("date") == today_str:
                    return data.get("sent", [])
        except:
            pass
    return []

def save_sent_alert(ticker):
    today_str = datetime.now().strftime("%Y-%m-%d")
    sent = load_sent_alerts()
    if ticker not in sent:
        sent.append(ticker)
    try:
        with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"date": today_str, "sent": sent}, f)
    except Exception as e:
        print(f"שגיאה בשמירת קובץ הזיכרון: {e}")

def check_volatility_alerts():
    if not CHAT_ID:
        return
        
    sent_today = load_sent_alerts()
    new_alerts = []
    
    for ticker, (hebrew_name, eng_name) in TICKERS.items():
        if ticker in sent_today:
            continue
            
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="5d" if "BTC" in ticker else "2d")
            
            if len(history) < 2:
                continue
                
            prev_close = history['Close'].iloc[-2]
            current_price = history['Close'].iloc[-1]
            high_price = history['High'].iloc[-1]
            low_price = history['Low'].iloc[-1]
            
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            
            if abs(change_percent) >= 5.0:
                is_positive = change >= 0
                emoji_status = "🟢📈 זינוק חד!" if is_positive else "🔴📉 ירידה חדה!"
                sign = "+" if is_positive else ""
                price_suffix = "$" if "BTC" not in ticker and "TA125" not in ticker else (" USD" if "BTC" in ticker else " נקודות")
                
                line = (
                    f"{emoji_status}\n"
                    f"📊 {hebrew_name} ({ticker})\n"
                    f"🔹 שינוי: {sign}{change_percent:.2f}% ({sign}{change:,.2f})\n"
                    f"💵 מחיר: {current_price:,.2f}{price_suffix}\n"
                    f"🔼 גבוה: {high_price:,.2f} | 📉 נמוך: {low_price:,.2f}\n"
                    f"〰️〰️〰️〰️〰️〰️"
                )
                new_alerts.append((ticker, line))
        except Exception as e:
            print(f"שגיאה במניה {ticker}: {e}")
            continue
            
    if new_alerts:
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        report_body = "\n".join([line for _, line in new_alerts])
        full_message = f"⚠️ התראות תנודתיות בשוק (מעל 5%)!\n📅 {current_time}\n\n{report_body}"
        
        try:
            bot.send_message(CHAT_ID, full_message)
            for ticker, _ in new_alerts:
                save_sent_alert(ticker)
        except Exception as e:
            print(f"שגיאה בשליחת הודעה לטלגרם: {e}")

if __name__ == '__main__':
    check_volatility_alerts()

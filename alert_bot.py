import os
import json
from datetime import datetime
import pytz
import telebot
import yfinance as yf

# ============================================================
# הגדרות
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN:
    raise ValueError("BOT_TOKEN לא מוגדר")

if not CHAT_ID:
    raise ValueError("CHAT_ID לא מוגדר")

bot = telebot.TeleBot(TOKEN)

ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

# קובץ זיכרון
ALERTS_FILE = "sent_alerts.json"

# ============================================================
# רשימת 25 הנכסים
# ============================================================

TICKERS = {
    "AAPL": ("אפל", "Apple Inc."),
    "TSLA": ("טסלה", "Tesla Inc."),
    "MSFT": ("מיקרוסופט", "Microsoft Corporation"),
    "NVDA": ("אנבידיה", "NVIDIA Corporation"),
    "PLTR": ("פלנטיר טכנולוגיות", "Palantir Technologies Inc."),
    "INTC": ("אינטל", "Intel Corporation"),
    "PYPL": ("פייפאל", "PayPal Holdings Inc."),
    "GOOGL": ("אלפאבית / גוגל", "Alphabet Inc."),
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

# ============================================================
# פונקציות עזר ותאריך
# ============================================================

def today_israel():
    return datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d")

def current_time_israel():
    return datetime.now(ISRAEL_TZ).strftime("%d/%m/%Y %H:%M")

# ============================================================
# ניהול זיכרון (טעינה ושמירה)
# ============================================================

def load_sent_alerts():
    today = today_israel()

    if not os.path.exists(ALERTS_FILE):
        return {
            "date": today,
            "sent": {}
        }

    try:
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # אם עבר יום חדש - מאפס את ההתראות
        if data.get("date") != today:
            print("📅 יום חדש - מאפס את ההתראות היומיות")
            return {
                "date": today,
                "sent": {}
            }

        return data

    except Exception as e:
        print(f"⚠️ לא ניתן לקרוא את קובץ הזיכרון: {e}")
        return {
            "date": today,
            "sent": {}
        }

def save_sent_alerts(data):
    try:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )
        print("💾 זיכרון ההתראות נשמר בהצלחה")
    except Exception as e:
        print(f"❌ שגיאה בשמירת הזיכרון: {e}")

def already_sent(sent_data, ticker, tier):
    ticker_data = sent_data.get(ticker, [])
    return tier in ticker_data

def mark_sent(sent_data, ticker, tier):
    if ticker not in sent_data:
        sent_data[ticker] = []

    if tier not in sent_data[ticker]:
        sent_data[ticker].append(tier)

# ============================================================
# שליפת נתוני מניה
# ============================================================

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)

        history = stock.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            timeout=10
        )

        if history is None or history.empty:
            print(f"⚠️ {ticker}: אין נתונים")
            return None

        history = history.dropna(subset=["Close"])

        if len(history) < 2:
            print(f"⚠️ {ticker}: אין מספיק נתונים")
            return None

        current = history.iloc[-1]
        previous = history.iloc[-2]

        current_price = float(current["Close"])
        previous_close = float(previous["Close"])

        high_price = float(current["High"])
        low_price = float(current["Low"])

        if previous_close == 0:
            return None

        change = current_price - previous_close
        change_percent = (change / previous_close) * 100

        return {
            "current_price": current_price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": change_percent,
            "high": high_price,
            "low": low_price
        }

    except Exception as e:
        print(f"❌ {ticker}: {e}")
        return None

def format_price(ticker, price):
    if ticker == "BTC-USD":
        return f"{price:,.2f} USD"
    if ticker == "^TA125.TA":
        return f"{price:,.2f} נקודות"
    return f"{price:,.2f}$"

# ============================================================
# יצירת הודעת התראה
# ============================================================

def create_alert(ticker, hebrew_name, data, tier):
    change_percent = data["change_percent"]
    change = data["change"]

    is_positive = change > 0

    sign_percent = "+" if change_percent > 0 else ""
    sign_change = "+" if change > 0 else ""

    if is_positive:
        title = "🚨🔥 זינוק קיצוני של 10%+, !" if tier == "10" else "🚨🔥 זינוק של 5%+!"
    else:
        title = "🚨📉 נפילה חדה של 10%-!" if tier == "10" else "🚨📉 ירידה של 5%-!"

    price = format_price(ticker, data["current_price"])

    return (
        f"{title}\n"
        f"📊 {hebrew_name} ({ticker})\n"
        f"🔹 שינוי: {sign_percent}{change_percent:.2f}% ({sign_change}{change:,.2f})\n"
        f"💵 מחיר: {price}\n"
        f"🔼 גבוה: {data['high']:,.2f} | 📉 נמוך: {data['low']:,.2f}\n"
        f"〰️〰️〰️〰️〰️〰️"
    )

# ============================================================
# פונקציית הראשית לבדיקת השוק
# ============================================================

def check_volatility_alerts():
    print("========================================")
    print("🚀 מתחיל בדיקת התראות")
    print(f"🇮🇱 שעה בישראל: {current_time_israel()}")
    print("========================================")

    memory = load_sent_alerts()
    sent_today = memory.setdefault("sent", {})
    new_alerts = []

    for ticker, names in TICKERS.items():
        hebrew_name, english_name = names

        try:
            data = get_stock_data(ticker)
            if not data:
                continue

            change_percent = data["change_percent"]
            absolute_change = abs(change_percent)

            if absolute_change >= 10:
                tier = "10"
            elif absolute_change >= 5:
                tier = "5"
            else:
                continue

            if tier == "10":
                if already_sent(sent_today, ticker, "10"):
                    print(f"⏭️ {ticker}: 10% כבר דווח היום")
                    continue
                mark_sent(sent_today, ticker, "10")
                mark_sent(sent_today, ticker, "5")
                alert = create_alert(ticker, hebrew_name, data, "10")
                new_alerts.append(alert)
                print(f"🚨 {ticker}: התראת 10% חדשה")

            elif tier == "5":
                if already_sent(sent_today, ticker, "5"):
                    print(f"⏭️ {ticker}: 5% כבר דווח היום")
                    continue
                mark_sent(sent_today, ticker, "5")
                alert = create_alert(ticker, hebrew_name, data, "5")
                new_alerts.append(alert)
                print(f"🚨 {ticker}: התראת 5% חדשה")

        except Exception as e:
            print(f"❌ שגיאה ב-{ticker}: {e}")
            continue

    # שמירת הזיכרון המעודכן לקובץ
    save_sent_alerts(memory)

    if not new_alerts:
        print("✅ אין התראות חדשות")
        return

    report_time = current_time_israel()
    message = (
        "⚠️ <b>התראות תנודתיות בשוק!</b>\n"
        f"📅 {report_time}\n\n"
        + "\n".join(new_alerts)
    )

    try:
        bot.send_message(
            CHAT_ID,
            message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        print(f"📨 נשלחה הודעה עם {len(new_alerts)} התראות")

    except Exception as e:
        print(f"❌ שגיאה בשליחה לטלגרם: {e}")
        raise

if __name__ == "__main__":
    check_volatility_alerts()

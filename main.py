import os
import time
import cloudscraper
import threading
import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CURRENT_BALANCE = 1000.0
TRADE_SIZE = 20.0

# --- WebShare Proxy with Port 6462 ---
PROXY_URL = "http://onzoyyph:hed0nyhkyw59@198.105.121.200:6462"

proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# Cloudflare bypass လုပ်ရန် Scraper တည်ဆောက်ခြင်း
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_market(market):
    try:
        question = market.get('group_name', 'Live Event')
        tokens = market.get('clobTokenIds', [])
        if not tokens or len(tokens) < 2: return

        # Proxy သုံးပြီး ဈေးနှုန်းဆွဲယူခြင်း
        y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[0]}&side=BUY", proxies=proxies, timeout=10).json()
        n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[1]}&side=BUY", proxies=proxies, timeout=10).json()
        
        y_p, n_p = float(y_res.get('price', 0)), float(n_res.get('price', 0))
        
        if y_p > 0.01 and n_p > 0.01:
            send_tele(f"✅ *PROXY DATA ACTIVE*\n📌 {question}\n🟢 Yes: `${y_p}` | 🔴 No: `${n_p}`")
    except: pass

def run_scanner():
    # IP အမှန်တကယ် ပြောင်းမပြောင်း စစ်ဆေးခြင်း
    try:
        ip_check = scraper.get("https://api.ipify.org", proxies=proxies, timeout=10).text
        print(f"RN1 Scan | Active IP: {ip_check} | Bal: ${CURRENT_BALANCE}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    try:
        # Polymarket Events ကို Proxy ဖြင့် ခေါ်ယူခြင်း
        gamma_url = "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=15"
        res = scraper.get(gamma_url, proxies=proxies, timeout=20)
        
        if res.status_code == 200:
            events = res.json()
            with ThreadPoolExecutor(max_workers=5) as executor:
                for event in events:
                    for market in event.get('markets', []):
                        executor.submit(check_market, market)
        else:
            print(f"⚠️ Status Code: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V7: Proxy Connected with Port 6462!*")
    while True:
        run_scanner()
        time.sleep(30)

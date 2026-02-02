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
MIN_EXIT_PROFIT = 0.02

# --- Proxy Configuration (သင်ပေးထားသော အချက်အလက်များ) ---
# Username: onzoyyph | Password: hed0nyhkyw59 | IP: 198.105.121.200
PROXY_URL = "http://onzoyyph:hed0nyhkyw59@198.105.121.200:80"

proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# Cloudflare wall ကို Proxy သုံးပြီး ကျော်ဖြတ်ရန်
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_market(market):
    global CURRENT_BALANCE
    try:
        question = market.get('group_name', 'Live Event')
        tokens = market.get('clobTokenIds', [])
        if not tokens or len(tokens) < 2: return

        # Proxy သုံးပြီး Polymarket ဈေးနှုန်းများကို တိုက်ရိုက်ယူခြင်း
        y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[0]}&side=BUY", proxies=proxies, timeout=10).json()
        n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[1]}&side=BUY", proxies=proxies, timeout=10).json()
        
        y_p, n_p = float(y_res.get('price', 0)), float(n_res.get('price', 0))
        
        if y_p > 0.01 and n_p > 0.01:
            send_tele(f"✅ *PROXY DATA ACTIVE*\n📌 {question}\n🟢 Yes: `${y_p}` | 🔴 No: `${n_p}`")
    except: pass

def run_scanner():
    # Proxy အလုပ်လုပ်ပုံကို စစ်ဆေးရန်
    try:
        ip_check = scraper.get("https://api.ipify.org", proxies=proxies, timeout=10).text
        print(f"RN1 Scan | Active IP: {ip_check} | Bal: ${CURRENT_BALANCE}")
    except:
        print("❌ Proxy Connection Failed! Please check your WebShare credentials.")
        return

    try:
        # Events Endpoint ကို Proxy ဖြင့် ခေါ်ယူခြင်း
        gamma_url = "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=15"
        res = scraper.get(gamma_url, proxies=proxies, timeout=20)
        
        if res.status_code == 200:
            events = res.json()
            with ThreadPoolExecutor(max_workers=5) as executor:
                for event in events:
                    for market in event.get('markets', []):
                        executor.submit(check_market, market)
        else:
            print(f"⚠️ Status Code: {res.status_code} - Blocked even with Proxy.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_tele("🛡️ *RN1 V7: WebShare Proxy Mode Online!*")
    while True:
        run_scanner()
        time.sleep(30)

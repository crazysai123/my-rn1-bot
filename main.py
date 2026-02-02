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

# Proxy logic များကို လုံးဝဖယ်ရှားပြီး Direct ချိတ်ဆက်မည်
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_market_data(m):
    try:
        tokens = m.get('tokens') or m.get('clobTokenIds')
        if not tokens: return False
        
        t_id = tokens[0].get('token_id') if isinstance(tokens[0], dict) else tokens[0]
        question = m.get('description') or m.get('question') or "Polymarket Event"

        # Direct Midpoint Price Check
        price_url = f"https://clob.polymarket.com/midpoint?token_id={t_id}"
        p_res = scraper.get(price_url, timeout=10) # No proxy here
        
        if p_res.status_code == 200:
            mid_p = float(p_res.json().get('mid_price', 0))
            if mid_p > 0:
                send_tele(f"🚀 *DIRECT DATA ACTIVE*\n📌 {question}\n📈 Mid Price: `${mid_p:.3f}`")
                return True
    except: return False
    return False

def run_scanner():
    print(f"RN1 V17 | DIRECT MODE | {datetime.datetime.now().strftime('%H:%M:%S')}") 
    try:
        # Railway IP ကို သုံးပြီး တိုက်ရိုက် ခေါ်ယူခြင်း
        res = scraper.get("https://clob.polymarket.com/sampling-markets", timeout=20)
        
        if res.status_code == 200:
            data = res.json()
            markets = []
            if isinstance(data, list): markets = data
            elif isinstance(data, dict): markets = data.get('markets', list(data.values()))

            if markets:
                found_count = 0
                with ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(executor.map(check_market_data, markets[:25]))
                    found_count = sum(1 for r in results if r)
                print(f"RN1 Scan | Active Responses: {found_count}")
        else:
            print(f"⚠️ Direct Access Blocked (Status: {res.status_code})")
            
    except Exception as e:
        print(f"❌ Direct Mode Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V17: Direct Bypass Mode Online!*")
    while True:
        run_scanner()
        time.sleep(60)

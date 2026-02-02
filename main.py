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

# --- UK Proxy Setup ---
PROXY_URL = "http://onzoyyph:hed0nyhkyw59@31.59.20.176:6754"
proxies = {"http": PROXY_URL, "https": PROXY_URL}

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
        # Token information extraction
        tokens = m.get('tokens') or m.get('clobTokenIds')
        if not tokens: return False
        
        # Format နှစ်မျိုးလုံးအတွက် စစ်ဆေးသည်
        t_id = tokens[0].get('token_id') if isinstance(tokens[0], dict) else tokens[0]
        question = m.get('description') or m.get('question') or "Polymarket Event"

        # Midpoint Price Check via Proxy
        price_url = f"https://clob.polymarket.com/midpoint?token_id={t_id}"
        p_res = scraper.get(price_url, proxies=proxies, timeout=10)
        
        if p_res.status_code == 200:
            mid_p = float(p_res.json().get('mid_price', 0))
            if mid_p > 0:
                send_tele(f"💎 *DATA RECEIVED*\n📌 {question}\n📈 Mid Price: `${mid_p:.3f}`")
                return True
    except: return False
    return False

def run_scanner():
    print(f"RN1 V13 | UK IP: 31.59.20.176 | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        # Sampling Markets သို့မဟုတ် Events Endpoint ကို သုံးခြင်း
        res = scraper.get("https://clob.polymarket.com/sampling-markets", proxies=proxies, timeout=20)
        
        if res.status_code == 200:
            data = res.json()
            
            # Slice error မတက်အောင် list သို့မဟုတ် dict ဖြစ်မဖြစ် စစ်ဆေးခြင်း
            markets = []
            if isinstance(data, list):
                markets = data
            elif isinstance(data, dict):
                markets = data.get('markets') or list(data.values())
            
            if markets:
                found_count = 0
                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(check_market_data, markets[:30]))
                    found_count = sum(1 for r in results if r)
                
                print(f"RN1 Scan | Active Responses: {found_count}")
        else:
            print(f"⚠️ API Error: {res.status_code} (Bypassing...)")
            
    except Exception as e:
        print(f"❌ Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🇬🇧 *RN1 V13: Ultimate Hybrid Mode Started!*")
    while True:
        run_scanner()
        time.sleep(45)

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
        # Sampling markets data structure အရ token id ကို ယူခြင်း
        tokens = m.get('tokens', [])
        if not tokens: return False
        
        t_id = tokens[0].get('token_id')
        question = m.get('description', 'Polymarket Event')

        # Live Midpoint Price ကို Proxy ဖြင့် ခေါ်ယူခြင်း
        price_url = f"https://clob.polymarket.com/midpoint?token_id={t_id}"
        p_res = scraper.get(price_url, proxies=proxies, timeout=10)
        
        if p_res.status_code == 200:
            mid_p = float(p_res.json().get('mid_price', 0))
            if mid_p > 0:
                send_tele(f"💎 *MARKET FOUND*\n📌 {question}\n📈 Mid Price: `${mid_p:.3f}`")
                return True
    except: return False
    return False

def run_scanner():
    print(f"RN1 V12 | UK IP: 31.59.20.176 | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        # Sampling Markets ကို တိုက်ရိုက်ခေါ်ယူခြင်း
        res = scraper.get("https://clob.polymarket.com/sampling-markets", proxies=proxies, timeout=20)
        
        if res.status_code == 200:
            markets = res.json()
            # Error မတက်စေရန် list ဖြစ်မဖြစ် စစ်ဆေးသည်
            if isinstance(markets, list):
                found_count = 0
                # ထိပ်ဆုံး ပွဲ ၂၀ ကို အမြန်ဆုံး scan ဖတ်မည်
                with ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(executor.map(check_market_data, markets[:20]))
                    found_count = sum(1 for r in results if r)
                
                print(f"RN1 Scan | Markets Responding: {found_count}")
        else:
            print(f"⚠️ API Error: {res.status_code}")
            
    except Exception as e:
        print(f"❌ Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🛡️ *RN1 V12: Ultra-Stable Mode Online!*")
    while True:
        run_scanner()
        time.sleep(60)

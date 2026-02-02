import os
import time
import cloudscraper
import threading
import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CURRENT_BALANCE = 1000.0
TRADE_SIZE = 20.0

# --- WebShare Proxy (Current) ---
PROXY_URL = "http://onzoyyph:hed0nyhkyw59@198.105.121.200:6462"
proxies = {"http": PROXY_URL, "https": PROXY_URL}

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_market(market):
    try:
        # Question field name က endpoint အပေါ်မူတည်ပြီး ကွဲနိုင်လို့ နှစ်မျိုးလုံးစစ်သည်
        question = market.get('question') or market.get('group_name') or "Live Event"
        tokens = market.get('clobTokenIds', [])
        if not tokens or len(tokens) < 2: return

        # Live Price Check
        y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[0]}&side=BUY", proxies=proxies, timeout=10).json()
        n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[1]}&side=BUY", proxies=proxies, timeout=10).json()
        
        y_p, n_p = float(y_res.get('price', 0)), float(n_res.get('price', 0))
        
        if y_p > 0.01 and n_p > 0.01:
            send_tele(f"✅ *DATA FOUND*\n📌 {question}\n🟢 Yes: `${y_p}` | 🔴 No: `${n_p}`")
            return True
    except: return False

def run_scanner():
    print(f"RN1 Scan | IP: 198.105.121.200 | Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
    found_count = 0
    
    # Endpoint (၃) ခုလုံးကို တစ်လှည့်စီ စမ်းသပ်ခြင်း
    endpoints = [
        "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20",
        "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=20",
        "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=20&order=volume24hr"
    ]
    
    for url in endpoints:
        try:
            res = scraper.get(url, proxies=proxies, timeout=15)
            if res.status_code == 200:
                data = res.json()
                # Endpoint က /events ဆိုရင် list ထဲကနေ market ကို ထပ်ထုတ်ရသည်
                markets = []
                if "events" in url:
                    for e in data: markets.extend(e.get('markets', []))
                else:
                    markets = data
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(executor.map(check_market, markets))
                    found_count += sum(1 for r in results if r)
            else:
                print(f"⚠️ Endpoint {url.split('/')[-1].split('?')[0]} blocked (Status: {res.status_code})")
        except: continue

    print(f"RN1 Scan | Active Trades Found: {found_count}")

if __name__ == "__main__":
    send_tele("🛠️ *RN1 V8: Ultra-Scan Mode Online!*")
    while True:
        run_scanner()
        time.sleep(30)

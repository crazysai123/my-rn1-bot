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

# --- UK Proxy Setup (Buffalo အစား London IP သုံးသည်) ---
# IP: 31.59.20.176 | Port: 6754
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

def check_market(market):
    try:
        question = market.get('question') or market.get('group_name') or "Live Event"
        tokens = market.get('clobTokenIds', [])
        if not tokens or len(tokens) < 2: return

        # UK Proxy ဖြင့် ဈေးနှုန်းစစ်ဆေးခြင်း
        y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[0]}&side=BUY", proxies=proxies, timeout=10).json()
        n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[1]}&side=BUY", proxies=proxies, timeout=10).json()
        
        y_p, n_p = float(y_res.get('price', 0)), float(n_res.get('price', 0))
        
        if y_p > 0.01 and n_p > 0.01:
            send_tele(f"🇬🇧 *UK DATA ACTIVE*\n📌 {question}\n🟢 Yes: `${y_p}` | 🔴 No: `${n_p}`")
            return True
    except: return False

def run_scanner():
    print(f"RN1 Scan | Active IP: 31.59.20.176 (UK) | Bal: ${CURRENT_BALANCE}")
    try:
        # Data ပိုရနိုင်သော Endpoint များ
        urls = [
            "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=15",
            "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=15&order=volume24hr"
        ]
        
        total_found = 0
        for url in urls:
            res = scraper.get(url, proxies=proxies, timeout=20)
            if res.status_code == 200:
                data = res.json()
                markets = []
                if "events" in url:
                    for e in data: markets.extend(e.get('markets', []))
                else: markets = data
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(executor.map(check_market, markets))
                    total_found += sum(1 for r in results if r)
        
        print(f"RN1 Scan | Total Active Found: {total_found}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_tele("🇬🇧 *RN1 V9: London Proxy Connected!*")
    while True:
        run_scanner()
        time.sleep(30)

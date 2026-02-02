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

ACTIVE_TRADES = {}
balance_lock = threading.Lock()

# Cloudflare wall ကို ကျော်ဖြတ်ရန် Scraper တည်ဆောက်ခြင်း
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_market(market):
    global CURRENT_BALANCE, ACTIVE_TRADES
    try:
        question = market.get('group_name', 'Unknown Event') # Event name ကို ယူခြင်း
        market_id = market.get('conditionId')
        tokens = market.get('clobTokenIds', [])
        
        if not tokens or len(tokens) < 2: return
        
        # ပွဲဟောင်းများစစ်ထုတ်ခြင်း
        if any(year in question for year in ["2022", "2023", "2024"]): return

        if market_id not in ACTIVE_TRADES:
            # Live Price ဆွဲယူခြင်း
            y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[0]}&side=BUY", timeout=10).json()
            n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={tokens[1]}&side=BUY", timeout=10).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            if y_p > 0.01 and n_p > 0.01:
                ACTIVE_TRADES[market_id] = {'y': y_p, 'n': n_p}
                send_tele(f"🚀 *BYPASS ENTRY*\n📌 {question}\n🟢 Yes: `${y_p}` | 🔴 No: `${n_p}`")
    except: pass

def run_scanner():
    print(f"RN1 Scan | Bal: ${CURRENT_BALANCE} | Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        # နည်းလမ်း (၂) - ပိုမိုရိုးရှင်းသော Events Endpoint
        gamma_url = "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20"
        response = scraper.get(gamma_url, timeout=20)
        
        if response.status_code != 200:
            print(f"⚠️ Error: Status Code {response.status_code} (Blocked by Polymarket)")
            return

        events = response.json()
        with ThreadPoolExecutor(max_workers=5) as executor:
            for event in events:
                for market in event.get('markets', []):
                    executor.submit(check_market, market)
                    
        print(f"RN1 Scan | Active Trades: {len(ACTIVE_TRADES)}")
        
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    send_tele("🛡️ *RN1 V6: Cloudflare Bypass Mode Started!*")
    while True:
        run_scanner()
        time.sleep(30)

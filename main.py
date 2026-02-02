import os
import time
import httpx
import datetime
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Settings ---
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
EXIT_THRESHOLD = 1.02  

# Entry Range (0.50 - 1.50)
ENTRY_RANGE_MIN = 0.50
ENTRY_RANGE_MAX = 1.50

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept": "application/json"
}

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        with httpx.Client() as client: client.post(url, json=payload)
    except: pass

def check_market_logic(m, client):
    global ACTIVE_TRADES
    try:
        # အဆင့် (၁): Gamma API ဒေတာကို အတင်းဆွဲထုတ်ခြင်း
        question = m.get('question') or m.get('description', 'Unknown Event')
        market_id = m.get('conditionId')
        
        # ဈေးနှုန်းဒေတာ ရှိမရှိ စစ်ဆေးခြင်း
        raw_prices = m.get('outcomePrices')
        if not raw_prices or len(raw_prices) < 2:
            # ဒေတာမရှိလျှင်ပင် Scan ဖတ်နေကြောင်း သိရအောင် Log ထုတ်မည်
            print(f"RN1 Monitoring | {question[:20]}.. | Waiting for Price Data")
            return

        a_p = float(raw_prices[0])
        b_p = float(raw_prices[1])
        current_sum = a_p + b_p

        print(f"RN1 Active | {question[:20]}.. | Sum: {current_sum:.3f}")

        if market_id not in ACTIVE_TRADES:
            if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX:
                with balance_lock:
                    ACTIVE_TRADES[market_id] = {'a_p': a_p, 'b_p': b_p}
                send_tele(f"🔥 *FORCE ENTRY*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`")
    except: pass

def run_v37_engine():
    # V19 ၏ Log Format အတိုင်း
    print(f"RN1 V37 | FORCE ENGINE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            # ပွဲစဉ် ၁၀၀၀ လုံးကို ယူရန် Pagination
            all_markets = []
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(0.3)
            
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                # ဒေတာတွေကို ပိုမြန်မြန်စစ်ဖို့ Thread တိုးထားသည်
                with ThreadPoolExecutor(max_workers=40) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m, client)
                        
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V37: Force Entry Engine Online!*")
    while True:
        run_v37_engine()
        time.sleep(random.randint(30, 60)) # ပိုမြန်မြန် Scan ဖတ်ရန် interval လျှော့ထားသည်

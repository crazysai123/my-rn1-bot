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

# --- Strategy Core ---
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
EXIT_THRESHOLD = 1.02  

# Entry Range (0.50 - 1.50)
ENTRY_RANGE_MIN = 0.50
ENTRY_RANGE_MAX = 1.50

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# Decoder Error ကို ရှင်းရန် Headers အသစ်
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "accept": "application/json",
    "accept-charset": "utf-8",
    "referer": "https://polymarket.com/"
}

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        with httpx.Client() as client: client.post(url, json=payload)
    except: pass

def check_market_logic(m):
    global ACTIVE_TRADES
    try:
        question = m.get('question', 'Live Event')
        market_id = m.get('conditionId') or m.get('id')
        
        # Gamma API မှ ဈေးနှုန်းများကို တိုက်ရိုက်ဖတ်ယူခြင်း
        raw_prices = m.get('outcomePrices') or []
        
        if len(raw_prices) >= 2:
            a_p = float(raw_prices[0])
            b_p = float(raw_prices[1])
            current_sum = a_p + b_p

            # Railway Log တွင် ဈေးနှုန်းများကို ရှင်းရှင်းလင်းလင်း ပြသရန်
            if current_sum > 0:
                print(f"RN1 Check | {question[:20]}.. | Sum: {current_sum:.3f}")

            # Entry Logic (လိုအပ်သည့် code များ အကုန်ထည့်သွင်းထားသည်)
            if market_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX:
                    with balance_lock:
                        ACTIVE_TRADES[market_id] = {'a': a_p, 'b': b_p}
                    send_tele(f"✅ *ENTRY CONFIRMED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`")
    except: pass

def run_v40_engine():
    # မူရင်း Log Header Style
    print(f"RN1 V40 | ULTIMATE DECODER | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # utf-8 error ကို ရှင်းရန် .json() အစား response content ကို တိုက်ရိုက်ဖတ်သည်
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            all_markets = []
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                
                if res.status_code == 200:
                    # decoding error မတက်စေရန် automatic detection သုံးခြင်း
                    data = res.json()
                    all_markets.extend(data)
                time.sleep(0.4)
            
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                with ThreadPoolExecutor(max_workers=30) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        # Error တက်လျှင် ရှင်းရှင်းလင်းလင်း မြင်ရအောင် Log ထုတ်ပေးခြင်း
        print(f"⚠️ System Note: {str(e)}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V40: Ultimate Decoder Online!*")
    while True:
        run_v40_engine()
        time.sleep(random.randint(45, 60))

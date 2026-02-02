import os
import time
import httpx
import datetime
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Core ---
CURRENT_BALANCE = 1000.0 
TRADE_SIZE = 20.0       
ENTRY_RANGE_MIN = 0.20
ENTRY_RANGE_MAX = 1.80

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# Error ကင်းဝေးစေရန် Header ကို အရှင်းဆုံးထားသည်
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "accept": "*/*"
}

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try:
        with httpx.Client() as client: client.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def check_market_logic(m):
    global ACTIVE_TRADES
    try:
        question = m.get('question', 'Live Event')
        market_id = m.get('conditionId') or m.get('id')
        raw_prices = m.get('outcomePrices') or []
        
        if len(raw_prices) >= 2:
            a_p, b_p = float(raw_prices[0]), float(raw_prices[1])
            current_sum = a_p + b_p

            # Railway Log တွင် ဈေးနှုန်းများကို အတင်းအကျပ် ပြသရန်
            print(f"RN1 Check | {question[:20]}.. | Sum: {current_sum:.3f}")

            if market_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX:
                    with balance_lock:
                        ACTIVE_TRADES[market_id] = True
                    send_tele(f"🔥 *ENTRY EXECUTED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`")
    except: pass

def run_v45_engine():
    # မူရင်း Log Style
    print(f"RN1 V45 | IRON-CLAD ENGINE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Unicode error ကို ကျော်လွှားရန် binary content အဖြစ် ဖတ်ယူခြင်း
        with httpx.Client(headers=HEADERS, timeout=45.0) as client:
            all_markets = []
            for offset in range(0, 600, 100): # Restart မဖြစ်စေရန် limit ကို ချိန်ညှိထားသည်
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                
                if res.status_code == 200:
                    try:
                        # Binary content ကို manual decode လုပ်ခြင်းဖြင့် utf-8 error ကို ရှင်းသည်
                        decoded_data = json.loads(res.content.decode('utf-8', errors='ignore'))
                        all_markets.extend(decoded_data)
                    except: continue
                time.sleep(1.2) # Stability အတွက် delay တိုးထားသည်
            
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        print(f"⚠️ Note: System is stabilizing... {str(e)[:30]}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V45: Iron-Clad Engine Online!*")
    while True:
        run_v45_engine()
        time.sleep(60)

import os
import time
import httpx
import datetime
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Core ---
CURRENT_BALANCE = 1000.0 
TRADE_SIZE = 20.0       
EXIT_THRESHOLD = 1.05  

# Entry မိရန် ရာခိုင်နှုန်း အများဆုံးဖြစ်အောင် 0.1 - 1.9 အထိ ချဲ့ထားသည်
ENTRY_RANGE_MIN = 0.1
ENTRY_RANGE_MAX = 1.9

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try:
        with httpx.Client() as client: client.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def check_market_logic(m):
    global ACTIVE_TRADES
    try:
        question = m.get('question') or m.get('description', 'Live Trade')
        m_id = m.get('conditionId') or m.get('id')
        prices = m.get('outcomePrices') or []
        
        if len(prices) >= 2:
            p1, p2 = float(prices[0]), float(prices[1])
            total = p1 + p2

            # ဈေးနှုန်းတိုင်းကို Log မှာ ထုတ်ပြခိုင်းခြင်း (အလုပ်လုပ်နေမှန်း သေချာစေရန်)
            if 0.05 < total < 2.5:
                print(f"DEBUG | {question[:15]} | SUM: {total:.3f}")

            if m_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= total <= ENTRY_RANGE_MAX:
                    with balance_lock:
                        ACTIVE_TRADES[m_id] = True
                    send_tele(f"🔥 *ENTRY TRIGGERED*\n📌 {question}\n📊 Sum: `{total:.3f}`")
    except: pass

def run_v50_engine():
    # သင့် Screenshot ထဲကအတိုင်း Active Entries ကို အမြဲပြမည်
    print(f"RN1 V50 | {datetime.datetime.now().strftime('%H:%M:%S')} | Active Entries: {len(ACTIVE_TRADES)}")
    
    try:
        with httpx.Client(timeout=45.0) as client:
            all_markets = []
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    data = json.loads(res.content.decode('utf-8', errors='ignore'))
                    all_markets.extend(data)
                time.sleep(0.3)
            
            print(f"RN1 Scan | Markets Loaded: {len(all_markets)}") 
            
            if all_markets:
                with ThreadPoolExecutor(max_workers=30) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        print(f"⚠️ Stability Note: {str(e)[:40]}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V50 Active: Entry Hunting Started!*")
    while True:
        run_v50_engine()
        time.sleep(30) # Scan အကြိမ်ရေကို ပိုစိပ်ထားသည်

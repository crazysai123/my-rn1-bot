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

# --- Strategy Core (မူရင်း Balance နှင့် Settings) ---
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
EXIT_THRESHOLD = 1.02  

# Entry Range ကို အစွမ်းကုန်ချဲ့ထားသည် (စမ်းသပ်ရန်)
ENTRY_RANGE_MIN = 0.50
ENTRY_RANGE_MAX = 1.50

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# Browser အစစ်ကဲ့သို့ Stealth Headers များ
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br",
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
        # ဒေတာအကုန်လုံးကို အတင်းအကျပ် ဆွဲထုတ်ခြင်း
        question = m.get('question') or m.get('description', 'Live Event')
        market_id = m.get('conditionId') or m.get('id')
        
        # Gamma API မှ Live Price များကို ယူသည်
        raw_prices = m.get('outcomePrices') or []
        
        if len(raw_prices) >= 2:
            a_p = float(raw_prices[0])
            b_p = float(raw_prices[1])
            current_sum = a_p + b_p

            # Railway Log တွင် ဈေးနှုန်းများကို ချက်ချင်းပြသရန် (မူရင်း V19 Style)
            if current_sum > 0:
                print(f"RN1 Check | {question[:20]}.. | Sum: {current_sum:.3f}")

            # Entry Logic (လိုအပ်သမျှ အကုန်ထည့်ထားသည်)
            if market_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX and current_sum > 0:
                    with balance_lock:
                        ACTIVE_TRADES[market_id] = {'a': a_p, 'b': b_p, 'q': question}
                    
                    # Telegram သို့ Entry တက်လာမည်
                    send_tele(f"🎯 *ENTRY EXECUTED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`\n💰 Size: `${TRADE_SIZE}`")
        else:
            # ဈေးနှုန်းမရပါကလည်း Log တွင် အချက်ပြမည်
            print(f"RN1 Scan | {question[:20]}.. | Waiting for Data")
            
    except Exception:
        pass

def run_v39_engine():
    # သင့် Screenshot ထဲက မူရင်း Log Header အတိုင်း
    print(f"RN1 V39 | FULL ENGINE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # httpx ကို decoding ကောင်းကောင်းလုပ်နိုင်အောင် config လုပ်ထားသည်
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0, follow_redirects=True) as client:
            all_markets = []
            # ပွဲစဉ် ၁၀၀၀ လုံးကို အပိုင်းလိုက် ဆွဲထုတ်ခြင်း
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(0.3)
            
            # မူရင်း Active Responses Log
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                # Thread ပမာဏကို မြှင့်ပြီး Entry ကို အမြန်ရှာခိုင်းသည်
                with ThreadPoolExecutor(max_workers=50) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V39: Full Entry Engine Online!*")
    while True:
        run_v39_engine()
        # Scan ဖတ်တဲ့ အကြိမ်ရေကို ပိုစိပ်စေရန် Interval လျှော့ထားသည်
        time.sleep(random.randint(30, 45))

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

# Entry ဝင်ဖို့ သေချာစေရန် Range ကို အကျယ်ဆုံးထားဆဲဖြစ်သည်
ENTRY_RANGE_MIN = 0.20
ENTRY_RANGE_MAX = 1.80

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# Browser အစစ်ကဲ့သို့ Stealth Headers
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br"
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
        question = m.get('question') or m.get('description', 'Live Event')
        market_id = m.get('conditionId') or m.get('id')
        raw_prices = m.get('outcomePrices') or []
        
        if len(raw_prices) >= 2:
            a_p, b_p = float(raw_prices[0]), float(raw_prices[1])
            current_sum = a_p + b_p

            # Railway Log တွင် Activity ပြသရန်
            if current_sum > 0:
                print(f"RN1 Check | {question[:20]}.. | Price: {current_sum:.3f}")

            # Entry Logic (လိုအပ်သည့် code များ အကုန်ထည့်ထားသည်)
            if market_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX:
                    with balance_lock:
                        ACTIVE_TRADES[market_id] = {'a': a_p, 'b': b_p}
                    
                    # Telegram သို့ ချက်ချင်းပို့မည်
                    send_tele(f"🎯 *ENTRY TRIGGERED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`")
    except: pass

def run_v44_engine():
    # မူရင်း Log Style မပျက်စေရန်
    print(f"RN1 V44 | STEALTH ENGINE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Memory ဝန်မပိစေရန် httpx client ကို စနစ်တကျ သုံးစွဲသည်
        with httpx.Client(http2=True, headers=HEADERS, timeout=30.0) as client:
            all_markets = []
            # ဒေတာများကို ပိုမိုစနစ်ကျသော batch ဖြင့် ဆွဲယူခြင်း
            for offset in range(0, 1000, 200):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=200&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(1.0) # Restart Loop ကို ကာကွယ်ရန် delay ထည့်ထားသည်
            
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                # Thread အရေအတွက်ကို Railway အခမဲ့ tier နှင့် ကိုက်ညီအောင် လျှော့ချထားသည်
                with ThreadPoolExecutor(max_workers=15) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        print(f"⚠️ Stability Note: {str(e)}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V44: Stealth Entry Engine Online!*")
    while True:
        run_v44_engine()
        # API Throttling မဖြစ်စေရန် အနားပေးချိန်ကို တိုးမြှင့်ထားသည်
        time.sleep(random.randint(60, 90))

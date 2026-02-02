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
EXIT_THRESHOLD = 1.02  

# Entry ဝင်ဖို့ အသေချာဆုံးဖြစ်အောင် Range ကို အစွမ်းကုန်ချဲ့ထားသည်
ENTRY_RANGE_MIN = 0.20
ENTRY_RANGE_MAX = 1.80

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# Decoder Error ကင်းဝေးစေရန် Header အပြည့်အစုံ
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "accept": "application/json",
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
        # ဒေတာများကို အစိမ်းလိုက်ဆွဲထုတ်ခြင်း
        question = m.get('question') or m.get('description', 'Live Event')
        market_id = m.get('conditionId') or m.get('id')
        raw_prices = m.get('outcomePrices') or []
        
        if len(raw_prices) >= 2:
            a_p, b_p = float(raw_prices[0]), float(raw_prices[1])
            current_sum = a_p + b_p

            # Railway Log မှာ ဈေးနှုန်းတိုင်းကို ပြသရန် (ဒီစာသားတက်လာရင် အလုပ်လုပ်နေပါပြီ)
            if current_sum > 0:
                print(f"TRACKER | {question[:25]}.. | Sum: {current_sum:.3f}")

            # Entry ဝင်မည့် Logic အပြည့်အစုံ
            if market_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX:
                    with balance_lock:
                        ACTIVE_TRADES[market_id] = {'a': a_p, 'b': b_p, 'q': question}
                    
                    # Telegram သို့ ချက်ချင်းအကြောင်းကြားခြင်း
                    msg = (f"🔥 *MEGA ENTRY EXECUTED*\n"
                           f"📌 {question}\n"
                           f"📊 Side A: `${a_p:.3f}`\n"
                           f"📊 Side B: `${b_p:.3f}`\n"
                           f"📈 Total Sum: `{current_sum:.3f}`")
                    send_tele(msg)
    except: pass

def run_v42_engine():
    # မူရင်း Log Header Style
    print(f"RN1 V42 | MEGA ENTRY | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            all_markets = []
            # ပွဲစဉ် ၁၀၀၀ လုံးကို အပိုင်းလိုက်ဆွဲယူခြင်း
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    try:
                        all_markets.extend(res.json())
                    except: continue
                time.sleep(0.3)
            
            # မူရင်း Active Responses Log
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                # Thread မြှင့်ပြီး အမြန်ဆုံး Entry ဝင်ခိုင်းခြင်း
                with ThreadPoolExecutor(max_workers=50) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        print(f"⚠️ Status: {str(e)}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V42: Mega-Entry Engine Active!*")
    while True:
        run_v42_engine()
        # အချိန်စောင့်ဆိုင်းမှုကို လျှော့ချပြီး အကြိမ်ရေများများ Scan ဖတ်ခိုင်းခြင်း
        time.sleep(30)

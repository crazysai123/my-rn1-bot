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

# သင်အလိုရှိသည့်အတိုင်း Entry Range ကို အစွန်းရောက်ချဲ့ထားသည် (စမ်းသပ်ရန်)
ENTRY_RANGE_MIN = 0.50
ENTRY_RANGE_MAX = 1.50

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept": "application/json",
    "referer": "https://polymarket.com/"
}

def send_tele(msg, show_balance_btn=False):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    if show_balance_btn:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": "💰 Check Total Balance", "callback_data": "get_balance"}]]}
    try:
        with httpx.Client() as client: client.post(url, json=payload)
    except: pass

def check_market_logic(m, client):
    global CURRENT_BALANCE, TOTAL_PROFIT, ACTIVE_TRADES
    try:
        # Gamma API မှ အခြေခံဈေးနှုန်းကို အရင်စစ်သည် (API ဝန်သက်သာစေရန်)
        raw_prices = m.get('outcomePrices', [])
        if len(raw_prices) < 2: return
        
        # အဆင့် (၁): ကိုက်ညီနိုင်ခြေရှိသော ပွဲများကိုသာ CLOB စစ်မည်
        question = m.get('question', 'Unknown Event')
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId') or m.get('condition_id')

        if market_id not in ACTIVE_TRADES:
            # API Rate Limit မမိစေရန် Delay အနည်းငယ်စီ ထည့်ထားသည်
            time.sleep(random.uniform(0.3, 0.8)) 
            
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={tokens[0]}&side=BUY").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={tokens[1]}&side=BUY").json()
            
            a_p, b_p = float(a_res.get('price', 0)), float(b_res.get('price', 0))
            current_sum = a_p + b_p

            # ဈေးနှုန်းရှိလျှင် Log တွင် ပြမည် (ဒါတက်လာမှ Bot အသက်ဝင်ခြင်းဖြစ်သည်)
            if current_sum > 0:
                print(f"RN1 Sharp-Scan | {question[:20]}.. | Sum: {current_sum:.3f}")

            # Entry Logic (ချဲ့ထားသော Range ဖြင့် စစ်ဆေးခြင်း)
            if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX and current_sum > 0:
                ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                send_tele(f"🚀 *ENTRY EXECUTED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`", True)

    except: pass

def run_v35_engine():
    # V19 ၏ Log Format အတိုင်း
    print(f"RN1 V35 | SHARP SCANNER | {datetime.datetime.now().strftime('%H:%M:%S')}")
    all_markets = []
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(0.5) 
            
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                # API ငြိမ်စေရန် Thread ကို ၁၅ ခုသာ ထားထားသည်
                with ThreadPoolExecutor(max_workers=15) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m, client)
                        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V35: Sharp Scanner (Ultra Range) Online!*", True)
    while True:
        run_v35_engine()
        time.sleep(random.randint(45, 75))

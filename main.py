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

# အခြေအနေ စမ်းသပ်ရန် Range ကို ကျယ်ကျယ်ထားဆဲဖြစ်သည်
ENTRY_RANGE_MIN = 0.95
ENTRY_RANGE_MAX = 1.10

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
        payload["reply_markup"] = {"inline_keyboard": [[{"text": "💰 Check Balance", "callback_data": "get_balance"}]]}
    try:
        with httpx.Client() as client: client.post(url, json=payload)
    except: pass

def check_market_logic(m, client):
    global CURRENT_BALANCE, TOTAL_PROFIT, ACTIVE_TRADES
    try:
        # Gamma API မှ ရသော အခြေခံဈေးနှုန်းကို အရင်စစ်ဆေးခြင်း (API Call သက်သာစေရန်)
        # Gamma API တွင် ဈေးနှုန်းမပါလျှင် CLOB ကို ဆက်မစစ်ဘဲ ကျော်မည်
        a_raw = m.get('outcomePrices', [0, 0])[0]
        b_raw = m.get('outcomePrices', [0, 0])[1]
        
        # အကြမ်းဖျင်း ပေါင်းလဒ်ကို အရင်ကြည့်သည်
        if not (0.90 <= (float(a_raw) + float(b_raw)) <= 1.15):
            return

        question = m.get('question', 'Unknown')
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId') or m.get('condition_id')
        a_id, b_id = tokens[0], tokens[1]

        if market_id not in ACTIVE_TRADES:
            # တကယ့် Buy Price ကို တောင်းယူခြင်း (တစ်စက္ကန့်လျှင် API Call အကန့်အသတ်ရှိသဖြင့် delay ထည့်ထားသည်)
            time.sleep(random.uniform(0.1, 0.5)) 
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=BUY").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=BUY").json()
            
            a_p, b_p = float(a_res.get('price', 0)), float(b_res.get('price', 0))
            current_sum = a_p + b_p

            # Log တွင် အမြဲပြနေစေရန်
            print(f"RN1 Check | {question[:20]}.. | Sum: {current_sum:.3f}")

            if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX and current_sum > 0:
                with balance_lock:
                    ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                send_tele(f"🚀 *ENTRY EXECUTED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`", True)

    except Exception as e:
        pass # Silent error for cleaner logs

def run_v34_engine():
    # V19 ၏ Log Format မူရင်းအတိုင်း
    print(f"RN1 V34 | SMART SCANNER | {datetime.datetime.now().strftime('%H:%M:%S')}")
    all_markets = []
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(0.5)
            
            # Screenshot အတိုင်း Active Response အရေအတွက်ပြခြင်း
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                # API ဝန်မပိစေရန် Thread ပမာဏကို ပြန်လျှော့ထားသည်
                with ThreadPoolExecutor(max_workers=15) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m, client)
                        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V34: Smart Scanner Online!*", True)
    while True:
        run_v34_engine()
        time.sleep(random.randint(45, 75))

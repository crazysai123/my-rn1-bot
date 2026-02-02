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

# --- Strategy Logic ---
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
EXIT_THRESHOLD = 1.02  

# Entry Range (0.95 - 1.10)
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
        payload["reply_markup"] = {"inline_keyboard": [[{"text": "💰 Check Total Balance", "callback_data": "get_balance"}]]}
    try:
        with httpx.Client() as client: client.post(url, json=payload)
    except: pass

def check_market_logic(m, client):
    global CURRENT_BALANCE, TOTAL_PROFIT, ACTIVE_TRADES
    try:
        question = m.get('question', 'Unknown Event')
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId') or m.get('condition_id')
        a_id, b_id = tokens[0], tokens[1]

        if market_id not in ACTIVE_TRADES:
            # Live Price Fetching
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=BUY").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=BUY").json()
            
            a_p = float(a_res.get('price', 0))
            b_p = float(b_res.get('price', 0))
            current_sum = a_p + b_p

            # --- DEBUG LOG (မူရင်း Log ထဲသို့ ထည့်သွင်းခြင်း) ---
            # ဈေးနှုန်းရှိသော ပွဲတိုင်းကို Railway Log တွင် ပြသပါမည်
            if current_sum > 0:
                short_q = (question[:25] + '..') if len(question) > 25 else question
                print(f"DEBUG | {short_q} | Sum: {current_sum:.3f}")

            # Entry Logic
            if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX:
                ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                send_tele(f"🚀 *ENTRY EXECUTED*\n📌 {question}\n📊 Sum: `{current_sum:.3f}`", True)

        elif market_id in ACTIVE_TRADES:
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=SELL").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=SELL").json()
            total_exit_sum = float(a_res.get('price', 0)) + float(b_res.get('price', 0))

            if total_exit_sum >= EXIT_THRESHOLD:
                net_profit = (TRADE_SIZE * total_exit_sum) - (TRADE_SIZE * 2) - GAS_BUFFER
                with balance_lock:
                    CURRENT_BALANCE += net_profit
                    TOTAL_PROFIT += net_profit
                    send_tele(f"💰 *PROFIT EXIT*\n📌 {question}\n📈 Net: `+${net_profit:.4f}`", True)
                    del ACTIVE_TRADES[market_id]
    except: pass

def run_v33_engine():
    # V19 ၏ မူရင်း Log Header
    print(f"RN1 V33 | GIANT SCAN (1000) | {datetime.datetime.now().strftime('%H:%M:%S')}")
    all_markets = []
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(0.5) 
            
            # မူရင်း Active Responses Log
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                with ThreadPoolExecutor(max_workers=50) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m, client)
                        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V33: Logger Active (1000 Events) Online!*", True)
    while True:
        run_v33_engine()
        time.sleep(random.randint(60, 90))

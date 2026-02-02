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
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
EXIT_THRESHOLD = 1.02  # A+B >= 1.02 ဖြစ်လျှင် Profit Exit

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# Stealth Headers (V19 မူရင်းအတိုင်း)
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept": "application/json",
    "referer": "https://polymarket.com/"
}

def send_tele(msg):
    if not TELE_TOKEN: return
    try:
        with httpx.Client() as client:
            client.post(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", 
                        json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def check_market_logic(m, client):
    global CURRENT_BALANCE, ACTIVE_TRADES
    try:
        question = m.get('question') or m.get('description', 'Live Event')
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId') or m.get('condition_id')
        a_id, b_id = tokens[0], tokens[1]

        # ၁။ Entry Check (A + B ≈ 1.00 တွင် ဝယ်ယူခြင်း)
        if market_id not in ACTIVE_TRADES:
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=BUY").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=BUY").json()
            a_p, b_p = float(a_res.get('price', 0)), float(b_res.get('price', 0))
            
            # Parity Check: 1.00 ဝန်းကျင်ဖြစ်မှ ဝင်မည်
            if 0.98 <= (a_p + b_p) <= 1.01:
                ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                send_tele(f"🛡️ *ENTRY AT PARITY*\n📌 {question}\n🔹 A: `${a_p}` | B: `${b_p}`\n📊 Sum: `${a_p + b_p:.3f}`")

        # ၂။ Exit Check (A + B >= 1.02 တွင် အမြတ်ထုတ်ခြင်း)
        elif market_id in ACTIVE_TRADES:
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=SELL").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=SELL").json()
            a_bid, b_bid = float(a_res.get('price', 0)), float(b_res.get('price', 0))
            total_exit_sum = a_bid + b_bid

            if total_exit_sum >= EXIT_THRESHOLD:
                net_profit = (TRADE_SIZE * total_exit_sum) - (TRADE_SIZE * 2) - GAS_BUFFER
                with balance_lock:
                    CURRENT_BALANCE += net_profit
                    send_tele(f"💰 *ARBITRAGE PROFIT*\n📌 {question}\n📤 Exit Sum: `${total_exit_sum:.3f}`\n📈 Net: `+${net_profit:.4f}`")
                    del ACTIVE_TRADES[market_id]
    except: pass

def run_v26_engine():
    # V19 ၏ မူရင်း Log Format အတိုင်း ပြန်လည်ပြင်ဆင်ထားသည်
    print(f"RN1 V26 | STEALTH ENGINE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=30.0) as client:
            # Active ပွဲစဉ်များကို ဆွဲယူခြင်း
            res = client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=20")
            
            if res.status_code == 200:
                markets = res.json()
                # မူရင်းအတိုင်း Active Responses အရေအတွက်ကို Log ပြမည်
                print(f"RN1 Scan | Active Responses: {len(markets)}")
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for m in markets:
                        executor.submit(check_market_logic, m, client)
            else:
                print(f"⚠️ API Status: {res.status_code}")
                
    except Exception as e:
        print(f"❌ Engine Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V26: Original Stealth + Arb Engine Online!*")
    while True:
        run_v26_engine()
        time.sleep(random.randint(45, 75))

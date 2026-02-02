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

# --- Arbitrage Logic Settings ---
CURRENT_BALANCE = 1000.0 
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
# A + B ပေါင်းလဒ် 1.02 ဖြစ်တာနဲ့ ရောင်းမည် (Arbitrage Trigger)
EXIT_THRESHOLD = 1.02  

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

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

        # ၁။ Entry Check (A + B ≈ 1.00 Parity တွင် ဝယ်ယူခြင်း)
        if market_id not in ACTIVE_TRADES:
            # Side A နှင့် B ၏ Buy Price ကို စစ်ဆေးခြင်း
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=BUY").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=BUY").json()
            
            a_p = float(a_res.get('price', 0))
            b_p = float(b_res.get('price', 0))
            total_entry_sum = a_p + b_p

            # ဈေးနှုန်းနှစ်ခုပေါင်း 1.00 ဝန်းကျင် ဖြစ်မှသာ ဝင်မည်
            if 0.98 <= total_entry_sum <= 1.01:
                ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p}
                entry_msg = (
                    f"🛡️ *ENTRY AT PARITY (1.00)*\n📌 {question}\n"
                    f"----------------------------\n"
                    f"🔹 Side A: `${a_p:.3f}` | 🔸 Side B: `${b_p:.3f}`\n"
                    f"📊 Total Cost: `${total_entry_sum:.3f}`\n"
                    f"💰 Amount: `${TRADE_SIZE * 2}`"
                )
                send_tele(entry_msg)
                return

        # ၂။ Dynamic Exit Check (မည်သည့် အခြေအနေမျိုးမဆို ပေါင်းလဒ် 1.02 ကျော်လျှင် ထွက်မည်)
        a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=SELL").json()
        b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=SELL").json()
        a_bid, b_bid = float(a_res.get('price', 0)), float(b_res.get('price', 0))
        total_exit_sum = a_bid + b_bid

        # ပေါင်းလဒ်သည် 1.02 ဖြစ်စေ၊ ထို့ထက်ပိုစေ ချက်ချင်း ရောင်းထုတ်မည်
        if total_exit_sum >= EXIT_THRESHOLD:
            net_profit = (TRADE_SIZE * total_exit_sum) - (TRADE_SIZE * 2) - GAS_BUFFER
            
            with balance_lock:
                CURRENT_BALANCE += net_profit
                exit_msg = (
                    f"💰 *DYNAMIC ARBITRAGE EXIT*\n📌 {question}\n"
                    f"----------------------------\n"
                    f"📤 Exit A: `${a_bid:.3f}` | B: `${b_bid:.3f}`\n"
                    f"📈 *Exit Sum: {total_exit_sum:.3f}* (Target: {EXIT_THRESHOLD})\n"
                    f"💵 Net Profit: `+${net_profit:.4f}`\n"
                    f"💳 Total Balance: `${CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_v25_engine():
    print(f"RN1 V25 | UNIVERSAL SUM ARB | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=30.0) as client:
            res = client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=30")
            if res.status_code == 200:
                markets = res.json()
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for m in markets:
                        executor.submit(check_market_logic, m, client)
    except Exception as e:
        print(f"❌ Engine Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V25: Universal Arbitrage Engine Online!*")
    while True:
        run_v25_engine()
        # Pattern ဖျောက်ရန် Random Interval သုံးခြင်း
        time.sleep(random.randint(45, 75))

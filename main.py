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
INITIAL_BALANCE = 1000.0
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
EXIT_THRESHOLD = 1.02  

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
    payload = {
        "chat_id": TELE_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    
    # Balance စစ်ဖို့ Button ထည့်ခြင်း
    if show_balance_btn:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": "💰 Check Total Balance", "callback_data": "get_balance"}]]
        }
        
    try:
        with httpx.Client() as client:
            client.post(url, json=payload)
    except: pass

def check_market_logic(m, client):
    global CURRENT_BALANCE, TOTAL_PROFIT, ACTIVE_TRADES
    try:
        question = m.get('question') or m.get('description', 'Live Event')
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId') or m.get('condition_id')
        a_id, b_id = tokens[0], tokens[1]

        # ၁။ Entry Check (ဈေးနှုန်းအတိအကျဖြင့် မှတ်သားခြင်း)
        if market_id not in ACTIVE_TRADES:
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=BUY").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=BUY").json()
            a_p, b_p = float(a_res.get('price', 0)), float(b_res.get('price', 0))
            
            if 0.98 <= (a_p + b_p) <= 1.01:
                ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                entry_msg = (
                    f"🛡️ *ENTRY EXECUTED*\n"
                    f"📌 *Event:* {question}\n"
                    f"----------------------------\n"
                    f"🔹 *Side A:* `${a_p:.3f}`\n"
                    f"🔸 *Side B:* `${b_p:.3f}`\n"
                    f"📊 *Entry Sum:* `${a_p + b_p:.3f}`\n"
                    f"💵 *Amount:* `${TRADE_SIZE * 2}`"
                )
                send_tele(entry_msg, show_balance_btn=True)

        # ၂။ Profit Exit (ဈေးနှုန်းအတိအကျဖြင့် ထွက်ခြင်း)
        elif market_id in ACTIVE_TRADES:
            a_res = client.get(f"https://clob.polymarket.com/price?token_id={a_id}&side=SELL").json()
            b_res = client.get(f"https://clob.polymarket.com/price?token_id={b_id}&side=SELL").json()
            a_bid, b_bid = float(a_res.get('price', 0)), float(b_res.get('price', 0))
            total_exit_sum = a_bid + b_bid

            if total_exit_sum >= EXIT_THRESHOLD:
                entry_data = ACTIVE_TRADES[market_id]
                net_profit = (TRADE_SIZE * total_exit_sum) - (TRADE_SIZE * 2) - GAS_BUFFER
                
                with balance_lock:
                    CURRENT_BALANCE += net_profit
                    TOTAL_PROFIT += net_profit
                    exit_msg = (
                        f"💰 *PROFIT EXIT*\n"
                        f"📌 *Event:* {question}\n"
                        f"----------------------------\n"
                        f"📥 *Entry A+B:* `${entry_data['a_entry'] + entry_data['b_entry']:.3f}`\n"
                        f"📤 *Exit A:* `${a_bid:.3f}` | *B:* `${b_bid:.3f}`\n"
                        f"📈 *Exit Sum:* `${total_exit_sum:.3f}`\n"
                        f"💵 *Net Profit:* `+${net_profit:.4f}`"
                    )
                    send_tele(exit_msg, show_balance_btn=True)
                    del ACTIVE_TRADES[market_id]
    except: pass

# Balance ကို အချိန်မရွေး ကြည့်နိုင်ရန် Function (Manual trigger via logic/status)
def get_balance_report():
    return (
        f"📊 *TOTAL PERFORMANCE REPORT*\n"
        f"----------------------------\n"
        f"💳 *Initial Capital:* `$1000.00`\n"
        f"💰 *Total Profit:* `+${TOTAL_PROFIT:.4f}`\n"
        f"💳 *Current Balance:* `${CURRENT_BALANCE:.2f}`\n"
        f"🎯 *Active Trades:* `{len(ACTIVE_TRADES)}`"
    )

def run_v27_engine():
    print(f"RN1 V27 | STEALTH + BUTTON | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=30.0) as client:
            res = client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=20")
            if res.status_code == 200:
                markets = res.json()
                print(f"RN1 Scan | Active Responses: {len(markets)}") # မူရင်း Active Response ပြရန်
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for m in markets:
                        executor.submit(check_market_logic, m, client)
            
            # ၁ နာရီတစ်ခါ Balance အလိုအလျောက် ပို့ပေးခြင်း (Optional)
            if datetime.datetime.now().minute == 0:
                send_tele(get_balance_report(), show_balance_btn=True)
                time.sleep(60)
                
    except Exception as e:
        print(f"❌ Engine Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V27: Arbitrage Pro Tracker Online!*", show_balance_btn=True)
    while True:
        run_v27_engine()
        time.sleep(random.randint(45, 75))

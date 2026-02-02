import os
import time
import requests
import threading
import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy & Risk Logic ---
# သင်အလိုရှိသည့်အတိုင်း $1000 Capital နှင့် $20 Trade Size
CURRENT_BALANCE = 1000.0 
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()
session = requests.Session()

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_spread_strategy(market):
    global CURRENT_BALANCE, ACTIVE_TRADES
    try:
        # Gamma API Field များအရ တိကျစွာဖတ်ယူခြင်း
        question = market.get('question', '')
        market_id = market.get('conditionId')
        
        # ဈေးနှုန်းရှိနိုင်သော Token ID များကို ရယူခြင်း
        tokens = market.get('clobTokenIds', [])
        if not tokens or len(tokens) < 2: return
        
        y_id, n_id = tokens[0], tokens[1]
        
        # ၁။ Entry Check: Midpoint Price ကို စစ်ဆေးခြင်း
        if market_id not in ACTIVE_TRADES:
            # BUY side ဈေးနှုန်းကို တိုက်ရိုက်ခေါ်ယူသည်
            y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=10).json()
            n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=10).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            # ဈေးနှုန်းအမှန်တကယ်ရှိပြီး ၂၀၂၃ ပွဲမဟုတ်မှသာ Entry ဝင်မည်
            if y_p > 0.01 and n_p > 0.01 and "2023" not in question:
                ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p, 'q': question}
                
                entry_msg = (
                    f"🎯 *LIVE ORDERBOOK ENTRY*\n"
                    f"📌 {question}\n"
                    f"----------------------------\n"
                    f"🟢 Yes Entry: `${y_p:.3f}`\n"
                    f"🔴 No Entry: `${n_p:.3f}`\n"
                    f"💵 Size: `${TRADE_SIZE}` | Bal: `${CURRENT_BALANCE}`"
                )
                send_tele(entry_msg)
                return

        # ၂။ Exit Check: Profit တွက်ချက်ခြင်း
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=10).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=10).json()
        y_bid, n_bid = float(y_res.get('price', 0)), float(n_res.get('price', 0))

        if (y_bid + n_bid) > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * (y_bid + n_bid)) - (TRADE_SIZE * 2) - GAS_BUFFER
            with balance_lock:
                CURRENT_BALANCE += net_profit
                exit_msg = (
                    f"💰 *PROFIT TAKEN*\n"
                    f"📌 {question}\n"
                    f"📥 Entry Sum: `${ACTIVE_TRADES[market_id]['y_entry'] + ACTIVE_TRADES[market_id]['n_entry']:.3f}`\n"
                    f"📤 Exit Sum: `${y_bid + n_bid:.3f}`\n"
                    f"💵 Net: `+${net_profit:.4f}` | Bal: `{CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_scanner():
    # Log တွင် အခြေအနေပြရန်
    print(f"RN1 Scan | Bal: ${CURRENT_BALANCE:.2f} | Active: {len(ACTIVE_TRADES)} | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        # ဈေးနှုန်းအစစ်အမှန်ရှိသော Markets များကိုသာ Gamma API မှ ဆွဲယူခြင်း
        # Active=true နှင့် closed=false ကို သေချာပေါက် သုံးထားသည်
        gamma_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=volume24hr"
        res = session.get(gamma_url, timeout=20).json()
        
        # Volume အများဆုံးပွဲများကို ဦးစားပေး ရှာဖွေမည်
        with ThreadPoolExecutor(max_workers=10) as executor:
            for m in res:
                if m.get('clobTokenIds') and len(m.get('clobTokenIds')) >= 2:
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("⚡ *RN1 V4: Orderbook Engine Started!*")
    while True:
        run_scanner()
        time.sleep(20) # API Limit မမိစေရန် အချိန်ပိုပေးထားသည်

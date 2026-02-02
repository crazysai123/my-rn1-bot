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
        # Gamma API Structure အရ field များ ပြောင်းလဲခြင်း
        question = market.get('question', '')
        market_id = market.get('conditionId')
        
        # Binary tokens (Yes/No) ရှိမရှိ စစ်ဆေးခြင်း
        tokens = market.get('clobTokenIds', [])
        if len(tokens) < 2: return
        
        y_id, n_id = tokens[0], tokens[1]
        
        # ၁။ Entry Check: ဈေးနှုန်းဆွဲယူခြင်း
        if market_id not in ACTIVE_TRADES:
            y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=5).json()
            n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=5).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            # ဈေးနှုန်း $0.00 မဟုတ်မှသာ Telegram ပို့မည်
            if y_p > 0 and n_p > 0:
                ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p, 'q': question}
                
                entry_msg = (
                    f"🚀 *LIVE MARKET DETECTED*\n"
                    f"📌 {question}\n"
                    f"----------------------------\n"
                    f"🟢 Yes: `${y_p:.3f}` | 🔴 No: `${n_p:.3f}`\n"
                    f"💵 Size: `${TRADE_SIZE}` | Bal: `${CURRENT_BALANCE}`"
                )
                send_tele(entry_msg)
                return

        # ၂။ Exit Check: အမြတ်ရမရ စစ်ဆေးခြင်း
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=5).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=5).json()
        y_bid = float(y_res.get('price', 0))
        n_bid = float(n_res.get('price', 0))
        
        if (y_bid + n_bid) > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * (y_bid + n_bid)) - (TRADE_SIZE * 2) - GAS_BUFFER
            with balance_lock:
                CURRENT_BALANCE += net_profit
                exit_msg = (
                    f"💰 *PROFIT CAPTURED*\n"
                    f"📌 {question}\n"
                    f"💵 Net: `+${net_profit:.4f}` | Bal: `{CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_scanner():
    print(f"RN1 Scan | Bal: ${CURRENT_BALANCE:.2f} | Active: {len(ACTIVE_TRADES)}")
    try:
        # နည်းလမ်းသစ်: Gamma API ကိုသုံး၍ လက်ရှိ Active ဖြစ်နေသော Markets များကို တိုက်ရိုက်ယူခြင်း
        # ဤ API သည် ဈေးနှုန်းရှိသော လက်ရှိပွဲများကို ပိုမိုတိကျစွာ ပြပေးနိုင်ပါသည်
        gamma_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50"
        res = session.get(gamma_url, timeout=15).json()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            for m in res:
                if m.get('clobTokenIds'):
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🛠️ *RN1 V3: Gamma Engine Online!*")
    while True:
        run_scanner()
        time.sleep(15) # API Rate limit အတွက် အချိန်တိုးထားသည်

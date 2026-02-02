import os
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Spread Trading & Risk Logic ---
CURRENT_BALANCE = 100.0
PEAK_BALANCE = 100.0
DRAWDOWN_LIMIT = 0.5    # 50% Drawdown Limit
TRADE_SIZE = 10.0       # Entry size ($1.00 ဝယ်ရင်း)
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  # $1.02 ကျော်မှ အမြတ်ထုတ်မည်

balance_lock = threading.Lock()
session = requests.Session()

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_risk_management():
    global CURRENT_BALANCE, PEAK_BALANCE
    if CURRENT_BALANCE > PEAK_BALANCE:
        PEAK_BALANCE = CURRENT_BALANCE
    
    allowed_floor = PEAK_BALANCE * (1 - DRAWDOWN_LIMIT)
    if CURRENT_BALANCE <= allowed_floor:
        send_tele(f"🛑 *DRAWDOWN ALERT*\nBalance `${CURRENT_BALANCE}` dropped 50% from Peak `${PEAK_BALANCE}`. Stopping.")
        os._exit(1)

def check_spread_strategy(market):
    global CURRENT_BALANCE
    try:
        y_id = market['tokens'][0]['token_id']
        n_id = market['tokens'][1]['token_id']
        
        # ရောင်းမည့်ဈေး (Sell/Bid Price) ကို စစ်ဆေးခြင်း
        # အဆင့် ၁ မှာ $1.00 နဲ့ ဝယ်ထားပြီးသားဟု ယူဆသည်
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=3).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=3).json()
        
        y_bid = float(y_res.get('price', 0)) # ပြန်ရောင်းရမည့်ဈေး
        n_bid = float(n_res.get('price', 0)) # ပြန်ရောင်းရမည့်ဈေး
        current_exit_sum = y_bid + n_bid

        # အဆင့် ၃ - Exit Strategy: ပေါင်းလဒ် $1 ထက်ကျော်မှ အမြတ်ယူခြင်း
        if current_exit_sum > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * current_exit_sum) - TRADE_SIZE - GAS_BUFFER
            
            with balance_lock:
                check_risk_management()
                CURRENT_BALANCE += net_profit
                msg = (
                    f"💰 *SPREAD PROFIT CAPTURED*\n"
                    f"📌 {market.get('question')}\n"
                    f"----------------------------\n"
                    f"📈 Exit Sum: `${current_exit_sum:.3f}`\n"
                    f"💵 Profit: `+${net_profit:.4f}`\n"
                    f"💳 Bal: `${CURRENT_BALANCE:.2f}`"
                )
                send_tele(msg)
    except: pass

def run_scanner():
    print(f"RN1 Spread Scan | Bal: ${CURRENT_BALANCE:.2f} | Peak: ${PEAK_BALANCE:.2f}")
    try:
        res = session.get("https://clob.polymarket.com/markets?active=true&limit=500", timeout=10).json()
        markets = res if isinstance(res, list) else res.get('data', [])
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            for m in markets:
                if 'tokens' in m and len(m['tokens']) >= 2:
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🎯 *Spread Capture Bot Online!* (Paper Trading Mode)")
    while True:
        run_scanner()
        time.sleep(10)

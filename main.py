import os
import time
import requests
import threading
import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy & Risk Logic ---
CURRENT_BALANCE = 1000.0 
PEAK_BALANCE = 1000.0
DRAWDOWN_LIMIT = 0.5
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  

# --- Trackers ---
ACTIVE_TRADES = {} 
TOTAL_TRADES_TODAY = 0
TOTAL_PROFIT_TODAY = 0.0

balance_lock = threading.Lock()
session = requests.Session()

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_spread_strategy(market):
    global CURRENT_BALANCE, TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY, ACTIVE_TRADES
    try:
        question = market.get('question', '')
        # Sports သာမက လက်ရှိ Active ဖြစ်နေသော Event အားလုံးကိုပါ ကြည့်ရှုရန်
        market_id = market.get('condition_id')
        tokens = market.get('tokens', [])
        if len(tokens) < 2: return

        y_id = tokens[0]['token_id']
        n_id = tokens[1]['token_id']
        
        # ၁။ Entry Check: Mid-point price ကို အရင်စစ်ဆေးခြင်း
        if market_id not in ACTIVE_TRADES:
            # Price ကို BUY side ကနေ တိုက်ရိုက်ယူသည်
            y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=5).json()
            n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=5).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            # ဈေးနှုန်း အမှန်တကယ် ရှိမှသာ Entry Message ပို့မည်
            if y_p > 0 and n_p > 0:
                ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p}
                
                entry_msg = (
                    f"🏟️ *LIVE MARKET ENTRY*\n"
                    f"📌 {question}\n"
                    f"----------------------------\n"
                    f"🟢 Yes: `${y_p:.3f}` | 🔴 No: `${n_p:.3f}`\n"
                    f"💵 Trade: `${TRADE_SIZE}` | Bal: `${CURRENT_BALANCE}`"
                )
                send_tele(entry_msg)
                return

        # ၂။ Exit Check: Profit logic
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=5).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=5).json()
        y_bid = float(y_res.get('price', 0))
        n_bid = float(n_res.get('price', 0))
        current_exit_sum = y_bid + n_bid

        if current_exit_sum > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * current_exit_sum) - (TRADE_SIZE * 2) - GAS_BUFFER
            entry_data = ACTIVE_TRADES.get(market_id)

            with balance_lock:
                CURRENT_BALANCE += net_profit
                TOTAL_TRADES_TODAY += 1
                TOTAL_PROFIT_TODAY += net_profit
                
                exit_msg = (
                    f"💰 *PROFIT CAPTURED*\n"
                    f"📌 {question}\n"
                    f"📥 Entry Sum: `${entry_data['y_entry'] + entry_data['n_entry']:.3f}`\n"
                    f"📤 Exit Sum: `${current_exit_sum:.3f}`\n"
                    f"💵 Net: `+${net_profit:.4f}` | Bal: `{CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_scanner():
    print(f"RN1 Scan | Bal: ${CURRENT_BALANCE:.2f} | Active: {len(ACTIVE_TRADES)}")
    try:
        # နည်းလမ်းအသစ်: Active ဖြစ်နေသော Market list ကို ကွဲပြားသော Endpoint မှ ဆွဲယူခြင်း
        # 'active=true' အပြင် 'closed=false' နှင့် 'orderbook' ရှိသော markets များကို ဦးစားပေးသည်
        api_url = "https://clob.polymarket.com/markets?active=true&closed=false"
        res = session.get(api_url, timeout=15).json()
        
        # Data structure ကို စနစ်တကျ စစ်ဆေးခြင်း
        markets = []
        if isinstance(res, list): markets = res
        elif isinstance(res, dict): markets = res.get('data', [])

        if not markets:
            print("No active markets found in current fetch.")
            return

        with ThreadPoolExecutor(max_workers=10) as executor:
            for m in markets:
                # Token နှစ်ခုလုံး ပါဝင်သော Binary Markets များကိုသာ စစ်ဆေးမည်
                if m.get('tokens') and len(m['tokens']) >= 2:
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🎯 *RN1 V2: Advanced Market Fetcher Online!*")
    while True:
        run_scanner()
        time.sleep(10) # API Rate limit မမိစေရန် ၁၀ စက္ကန့်ခြားသည်

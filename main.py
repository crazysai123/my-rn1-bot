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
CURRENT_BALANCE = 100.0
PEAK_BALANCE = 100.0
DRAWDOWN_LIMIT = 0.5    
TRADE_SIZE = 10.0       
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  # $1.02 ကျော်မှ အမြတ်ယူရန်

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

def check_risk_management():
    global CURRENT_BALANCE, PEAK_BALANCE
    if CURRENT_BALANCE > PEAK_BALANCE:
        PEAK_BALANCE = CURRENT_BALANCE
    allowed_floor = PEAK_BALANCE * (1 - DRAWDOWN_LIMIT)
    if CURRENT_BALANCE <= allowed_floor:
        send_tele(f"🛑 *DRAWDOWN ALERT*\nBalance `${CURRENT_BALANCE:.2f}` dropped 50% from Peak.")
        os._exit(1)

def send_daily_report():
    global TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY
    now = datetime.datetime.now()
    if now.hour == 9 and now.minute == 0:
        report_msg = (
            f"📅 *DAILY PERFORMANCE REPORT*\n"
            f"🎯 Total Profits Taken: `{TOTAL_TRADES_TODAY}`\n"
            f"💰 Daily Profit: `+${TOTAL_PROFIT_TODAY:.4f}`\n"
            f"💳 Balance: `${CURRENT_BALANCE:.2f}`"
        )
        send_tele(report_msg)
        TOTAL_TRADES_TODAY = 0
        TOTAL_PROFIT_TODAY = 0.0
        time.sleep(61)

def check_spread_strategy(market):
    global CURRENT_BALANCE, TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY, ACTIVE_TRADES
    try:
        question = market.get('question', '')
        # Sports Filter ကို ပိုကျယ်ပြန့်အောင် ပြင်ဆင်ခြင်း
        is_sports = any(word in question.lower() for word in ['vs', 'win', 'match', 'game', 'cup', 'league', 'at', 'tournament'])
        if not is_sports: return

        market_id = market.get('condition_id')
        y_id = market['tokens'][0]['token_id']
        n_id = market['tokens'][1]['token_id']
        
        # ၁။ Entry Check: ဈေးနှုန်းမှန်ကန်စွာ ဆွဲယူခြင်း
        if market_id not in ACTIVE_TRADES:
            y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=3).json()
            n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=3).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            # ဈေးနှုန်း 0.00 မဟုတ်မှသာ Entry ဝင်မည်
            if y_p <= 0.01 or n_p <= 0.01: return

            ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p}
            
            entry_msg = (
                f"🏟️ *NEW ENTRY (SPORTS)*\n"
                f"📌 {question}\n"
                f"----------------------------\n"
                f"🟢 Yes Entry: `${y_p:.3f}`\n"
                f"🔴 No Entry: `${n_p:.3f}`\n"
                f"💵 Total Capital: `$1.000`"
            )
            send_tele(entry_msg)
            return

        # ၂။ Exit Check: Targeted Profit Message (Entry/Exit ဈေးနှုန်းများယှဉ်ပြရန်)
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=3).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=3).json()
        
        y_bid = float(y_res.get('price', 0))
        n_bid = float(n_res.get('price', 0))
        current_exit_sum = y_bid + n_bid

        if current_exit_sum > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * current_exit_sum) - TRADE_SIZE - GAS_BUFFER
            entry_data = ACTIVE_TRADES.get(market_id)

            with balance_lock:
                check_risk_management()
                CURRENT_BALANCE += net_profit
                TOTAL_TRADES_TODAY += 1
                TOTAL_PROFIT_TODAY += net_profit
                
                # Targeted Profit Message
                exit_msg = (
                    f"💰 *PROFIT CAPTURED (1.0+)*\n"
                    f"📌 {question}\n"
                    f"----------------------------\n"
                    f"📥 *Entry:* Y: `${entry_data['y_entry']:.2f}` | N: `${entry_data['n_entry']:.2f}`\n"
                    f"📤 *Exit:* Y: `${y_bid:.2f}` | N: `${n_bid:.2f}`\n"
                    f"📈 Total Sum: `${current_exit_sum:.3f}`\n"
                    f"----------------------------\n"
                    f"💵 Net Profit: `+${net_profit:.4f}`\n"
                    f"💳 Total Balance: `{CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_scanner():
    send_daily_report()
    # Active ပွဲအရေအတွက်ကို Log မှာပြရန်
    print(f"RN1 Scan | Bal: ${CURRENT_BALANCE:.2f} | Active Trades: {len(ACTIVE_TRADES)}")
    try:
        res = session.get("https://clob.polymarket.com/markets?active=true&limit=1000", timeout=10).json()
        markets = res if isinstance(res, list) else res.get('data', [])
        with ThreadPoolExecutor(max_workers=20) as executor:
            for m in markets:
                if 'tokens' in m and len(m['tokens']) >= 2:
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🎯 *RN1 Professional Sports Bot Online!*")
    while True:
        run_scanner()
        time.sleep(5)

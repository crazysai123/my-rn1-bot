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

def check_risk_management():
    global CURRENT_BALANCE, PEAK_BALANCE
    if CURRENT_BALANCE > PEAK_BALANCE:
        PEAK_BALANCE = CURRENT_BALANCE
    allowed_floor = PEAK_BALANCE * (1 - DRAWDOWN_LIMIT)
    if CURRENT_BALANCE <= allowed_floor:
        send_tele(f"🛑 *DRAWDOWN ALERT*\nBalance `${CURRENT_BALANCE}` dropped 50% from Peak.")
        os._exit(1)

def send_daily_report():
    global TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY
    now = datetime.datetime.now()
    if now.hour == 9 and now.minute == 0:
        report_msg = (
            f"📅 *DAILY PERFORMANCE REPORT*\n"
            f"🎯 Total Profits Taken: `{TOTAL_TRADES_TODAY}`\n"
            f"💰 Daily Profit: `+${TOTAL_PROFIT_TODAY:.4f}`\n"
            f"💳 Balance: `{CURRENT_BALANCE:.2f}`"
        )
        send_tele(report_msg)
        TOTAL_TRADES_TODAY = 0
        TOTAL_PROFIT_TODAY = 0.0
        time.sleep(61)

def check_spread_strategy(market):
    global CURRENT_BALANCE, TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY, ACTIVE_TRADES
    try:
        question = market.get('question', '')
        # Sports Filter & 2026 Focus (ပွဲဟောင်းများ ဖယ်ထုတ်ရန်)
        is_sports = any(word in question.lower() for word in ['vs', 'win', 'match', 'game', 'tournament', 'cup', 'league'])
        is_old = any(yr in question for yr in ['2023', '2024', '2025'])
        if not is_sports or is_old: return

        market_id = market.get('condition_id')
        y_id = market['tokens'][0]['token_id']
        n_id = market['tokens'][1]['token_id']
        
        # ၁။ Entry Check: Yes/No ဈေးနှုန်း အတိအကျကို မှတ်သားခြင်း
        if market_id not in ACTIVE_TRADES:
            y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=3).json()
            n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=3).json()
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            # မူလ Entry ဈေးနှုန်းကို သိမ်းဆည်းခြင်း
            ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p}
            
            entry_msg = (
                f"🏟️ *NEW ENTRY (LIVE 2026)*\n"
                f"📌 {question}\n"
                f"----------------------------\n"
                f"🟢 Yes Entry: `${y_p:.3f}`\n"
                f"🔴 No Entry: `${n_p:.3f}`\n"
                f"💵 Total Capital: `$1.000`"
            )
            send_tele(entry_msg)
            print(f"Entry Start: {question}")
            return

        # ၂။ Exit Check: Profit ဈေးနှုန်း အတိအကျဖြင့် Message ပို့ခြင်း
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=3).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=3).json()
        y_bid = float(y_res.get('price', 0))
        n_bid = float(n_res.get('price', 0))
        current_exit_sum = y_bid + n_bid

        if current_exit_sum > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * current_exit_sum) - TRADE_SIZE - GAS_BUFFER
            entry_data = ACTIVE_TRADES.get(market_id) # မူလဝယ်ဈေး ပြန်ထုတ်ခြင်း

            with balance_lock:
                check_risk_management()
                CURRENT_BALANCE += net_profit
                TOTAL_TRADES_TODAY += 1
                TOTAL_PROFIT_TODAY += net_profit
                
                # Targeted Exit Message (Balance ကို နှိပ်၍ရအောင် ` ` သုံးထားသည်)
                exit_msg = (
                    f"💰 *PROFIT CAPTURED (1.0+)*\n"
                    f"📌 {question}\n"
                    f"----------------------------\n"
                    f"📥 *Entry Prices:* Y: `${entry_data['y_entry']:.3f}` | N: `${entry_data['n_entry']:.3f}`\n"
                    f"📤 *Exit Prices:* Y: `${y_bid:.3f}` | N: `${n_bid:.3f}`\n"
                    f"📈 Total Exit Sum: `${current_exit_sum:.3f}`\n"
                    f"----------------------------\n"
                    f"💵 Net Profit: `+${net_profit:.4f}`\n"
                    f"💳 Total Balance: `{CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_scanner():
    send_daily_report()
    print(f"RN1 Scan | Bal: ${CURRENT_BALANCE:.2f} | Active: {len(ACTIVE_TRADES)}")
    try:
        # လက်ရှိပွဲများကိုသာ ဆွဲယူရန် API URL
        api_url = "https://clob.polymarket.com/markets?active=true&closed=false&limit=100"
        res = session.get(api_url, timeout=10).json()
        markets = res if isinstance(res, list) else res.get('data', [])
        with ThreadPoolExecutor(max_workers=20) as executor:
            for m in markets:
                if 'tokens' in m and len(m['tokens']) >= 2:
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🎯 *RN1 Accurate 2026 Tracker Online!*")
    while True:
        run_scanner()
        time.sleep(5)

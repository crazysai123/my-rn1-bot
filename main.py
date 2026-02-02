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
DRAWDOWN_LIMIT = 0.5    # 50% Drawdown
TRADE_SIZE = 10.0       # $1.00 Entry အခြေခံ
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  # $1.02 ကျော်မှ အမြတ်ယူရန်

# --- Daily Report Tracker ---
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
        send_tele(f"🛑 *DRAWDOWN ALERT*\nBalance `${CURRENT_BALANCE}` dropped 50% from Peak `${PEAK_BALANCE}`.")
        os._exit(1)

def send_daily_report():
    global TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY
    now = datetime.datetime.now()
    
    # မနက် ၉ နာရီ (09:00) တွင် Report ပို့ရန် ပြောင်းလဲထားသည်
    if now.hour == 9 and now.minute == 0:
        report_msg = (
            f"📅 *DAILY PERFORMANCE REPORT*\n"
            f"*(Sent at 09:00 AM)*\n"
            f"----------------------------\n"
            f"🎯 Total Times Hit $1.02: `{TOTAL_TRADES_TODAY}`\n"
            f"💰 Total Daily Profit: `+${TOTAL_PROFIT_TODAY:.4f}`\n"
            f"💳 Current Balance: `${CURRENT_BALANCE:.2f}`\n"
            f"📈 Max Peak Reached: `${PEAK_BALANCE:.2f}`\n"
            f"----------------------------"
        )
        send_tele(report_msg)
        # Reset data for next 24 hours
        TOTAL_TRADES_TODAY = 0
        TOTAL_PROFIT_TODAY = 0.0
        time.sleep(61) # တစ်မိနစ်အတွင်း နှစ်ခါမပို့မိစေရန်

def check_spread_strategy(market):
    global CURRENT_BALANCE, TOTAL_TRADES_TODAY, TOTAL_PROFIT_TODAY
    try:
        y_id = market['tokens'][0]['token_id']
        n_id = market['tokens'][1]['token_id']
        
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", timeout=3).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", timeout=3).json()
        
        y_bid = float(y_res.get('price', 0))
        n_bid = float(n_res.get('price', 0))
        current_exit_sum = y_bid + n_bid

        # Entry $1.00 မှစတင်၍ $1.02 တွင် အမြတ်ယူခြင်း
        if current_exit_sum > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * current_exit_sum) - TRADE_SIZE - GAS_BUFFER
            
            with balance_lock:
                check_risk_management()
                CURRENT_BALANCE += net_profit
                TOTAL_TRADES_TODAY += 1
                TOTAL_PROFIT_TODAY += net_profit
                
                msg = (
                    f"💰 *SPREAD PROFIT CAPTURED*\n"
                    f"📌 {market.get('question')}\n"
                    f"🟢 Yes Sell: `${y_bid:.3f}` | 🔴 No Sell: `${n_bid:.3f}`\n"
                    f"📈 Exit Sum: `${current_exit_sum:.3f}`\n"
                    f"💵 Profit: `+${net_profit:.4f}`\n"
                    f"💳 Bal: `${CURRENT_BALANCE:.2f}`"
                )
                send_tele(msg)
    except: pass

def run_scanner():
    send_daily_report()
    print(f"RN1 Spread Scan | Bal: ${CURRENT_BALANCE:.2f} | Peak: ${PEAK_BALANCE:.2f}")
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
    send_tele("🎯 *RN1 Professional Spread Bot Online!*")
    while True:
        run_scanner()
        time.sleep(5) # ၅ စက္ကန့်တစ်ခါ အမြန်စစ်ဆေးခြင်း

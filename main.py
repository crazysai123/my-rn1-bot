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

# --- Paper Trading Logic ---
CURRENT_BALANCE = 100.0
TRADE_SIZE = 5.0      
GAS_BUFFER = 0.01     
MIN_NET_PROFIT = 0.02 # အမြတ်နည်းနည်းတွေ့တာနဲ့ Trade ရန် လျှော့ချထားသည်
PROFIT_MARGIN = 0.002 

balance_lock = threading.Lock()
session = requests.Session()

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_arbitrage(market):
    global CURRENT_BALANCE
    try:
        y_id = market['tokens'][0]['token_id']
        n_id = market['tokens'][1]['token_id']
        
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=3).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=3).json()
        
        y_p = float(y_res.get('price', 0))
        n_p = float(n_res.get('price', 0))
        total_sum = y_p + n_p

        if 0 < total_sum < (1.0 - PROFIT_MARGIN):
            net_profit = (TRADE_SIZE / total_sum) - TRADE_SIZE - GAS_BUFFER
            if net_profit >= MIN_NET_PROFIT:
                with balance_lock:
                    CURRENT_BALANCE += net_profit
                    msg = (
                        f"✅ *PAPER TRADE SUCCESS*\n"
                        f"📌 {market.get('question')}\n"
                        f"----------------------------\n"
                        f"🟢 Yes Price: `${y_p:.3f}`\n"
                        f"🔴 No Price: `${n_p:.3f}`\n"
                        f"📊 Total Cost: `${total_sum:.3f}`\n"
                        f"----------------------------\n"
                        f"💰 Profit: `+${net_profit:.4f}`\n"
                        f"💳 Bal: `${CURRENT_BALANCE:.2f}`"
                    )
                    send_tele(msg)
    except: pass

def run_scanner():
    print(f"RN1 High-Speed Scan | Bal: ${CURRENT_BALANCE:.2f}")
    try:
        # ပွဲပေါင်း ၁၀၀၀ အထိ အကုန်ဆွဲထုတ်ခြင်း
        res = session.get("https://clob.polymarket.com/markets?active=true&limit=1000", timeout=10).json()
        markets = res if isinstance(res, list) else res.get('data', [])
        
        # Thread ပေါင်း ၂၀ ဖြင့် အလွန်မြန်အောင် စစ်ဆေးခြင်း
        with ThreadPoolExecutor(max_workers=20) as executor:
            for m in markets:
                if 'tokens' in m and len(m['tokens']) >= 2:
                    executor.submit(check_arbitrage, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 Ultra High-Speed Scanner Online!*")
    while True:
        run_scanner()
        time.sleep(5) # ၅ စက္ကန့်တစ်ခါ အမြန် Loop ပတ်ရန်

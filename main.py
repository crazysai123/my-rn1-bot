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

# --- Paper Trading Logic ($100 Start) ---
START_BALANCE = 100.0
CURRENT_BALANCE = 100.0
TRADE_SIZE = 5.0      # Paper trade amount
GAS_BUFFER = 0.02     # Simulated Polygon fee
MIN_NET_PROFIT = 0.05 # Minimum profit to trigger log
PROFIT_MARGIN = 0.005 # Slippage protection buffer

balance_lock = threading.Lock()
session = requests.Session()

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_stop_loss():
    global CURRENT_BALANCE
    # Stop if virtual funds drop below 50%
    if CURRENT_BALANCE <= (START_BALANCE * 0.5):
        msg = f"🛑 *CRITICAL STOP-LOSS*\nBalance: `${CURRENT_BALANCE}`\nBot Paused."
        send_tele(msg)
        os._exit(1)

def check_arbitrage(market):
    global CURRENT_BALANCE
    try:
        title = market.get('question', 'Unknown Market')
        # Use stable REST API instead of WebSocket to avoid 404 error
        y_id = market['tokens'][0]['token_id']
        n_id = market['tokens'][1]['token_id']
        
        y_res = session.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", timeout=3).json()
        n_res = session.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", timeout=3).json()
        
        y_price = float(y_res.get('price', 0))
        n_price = float(n_res.get('price', 0))
        total_sum = y_price + n_price

        # Arbitrage Detection Logic
        if 0 < total_sum < (1.0 - PROFIT_MARGIN):
            gross_profit = (TRADE_SIZE / total_sum) - TRADE_SIZE
            net_profit = gross_profit - GAS_BUFFER

            if net_profit >= MIN_NET_PROFIT:
                with balance_lock:
                    check_stop_loss()
                    CURRENT_BALANCE += net_profit
                    msg = (
                        f"✅ *PAPER ARBITRAGE FOUND*\n"
                        f"📌 {title}\n"
                        f"💰 Profit: `+${net_profit:.4f}`\n"
                        f"💳 Virtual Bal: `${CURRENT_BALANCE:.2f}`"
                    )
                    send_tele(msg)
    except: pass

def run_scanner():
    print(f"RN1 Scan Loop | Bal: ${CURRENT_BALANCE:.2f}")
    try:
        # Fetching active markets
        res = session.get("https://clob.polymarket.com/markets?active=true", timeout=5).json()
        markets = res if isinstance(res, list) else res.get('data', [])
        
        # Parallel scanning for speed
        with ThreadPoolExecutor(max_workers=5) as executor:
            for m in markets[:20]: # Scan top 20 active markets
                executor.submit(check_arbitrage, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("🧪 *RN1 Paper Bot Started*\nSimulation Budget: `$100.00`")
    while True:
        run_scanner()
        time.sleep(10) # 10s interval to prevent rate limit

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

# --- Strategy Logic ($1000 Capital) ---
CURRENT_BALANCE = 1000.0 
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# --- Stealth Browser Headers ---
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept": "application/json",
    "referer": "https://polymarket.com/"
}

def send_tele(msg):
    if not TELE_TOKEN: return
    try:
        with httpx.Client() as client:
            client.post(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", 
                        json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def check_market_logic(m, client):
    global CURRENT_BALANCE, ACTIVE_TRADES
    try:
        question = m.get('question') or m.get('description', 'Live Event')
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        
        if not tokens or len(tokens) < 2: return
        market_id = m.get('conditionId') or m.get('condition_id')
        y_id, n_id = tokens[0], tokens[1]

        # ၁။ Entry Check (Buy Side)
        if market_id not in ACTIVE_TRADES:
            y_res = client.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY").json()
            n_res = client.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY").json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))

            if y_p > 0.01 and n_p > 0.01:
                ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p, 'q': question}
                entry_msg = (
                    f"🏟️ *TRADE ENTRY*\n📌 {question}\n"
                    f"----------------------------\n"
                    f"🟢 Yes: `${y_p:.3f}` | 🔴 No: `${n_p:.3f}`\n"
                    f"💰 Amount: `${TRADE_SIZE * 2}`\n"
                    f"💳 Balance: `${CURRENT_BALANCE:.2f}`"
                )
                send_tele(entry_msg)
                return

        # ၂။ Exit Check (Sell Side - Arbitrage Detection)
        y_res = client.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL").json()
        n_res = client.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL").json()
        y_bid, n_bid = float(y_res.get('price', 0)), float(n_res.get('price', 0))

        if (y_bid + n_bid) > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * (y_bid + n_bid)) - (TRADE_SIZE * 2) - GAS_BUFFER
            entry_data = ACTIVE_TRADES[market_id]
            
            with balance_lock:
                CURRENT_BALANCE += net_profit
                exit_msg = (
                    f"💰 *PROFIT EXIT*\n📌 {question}\n"
                    f"----------------------------\n"
                    f"📥 Entry Sum: `${entry_data['y_entry'] + entry_data['n_entry']:.3f}`\n"
                    f"📤 Exit Sum: `${y_bid + n_bid:.3f}`\n"
                    f"💵 Net Profit: `+${net_profit:.4f}`\n"
                    f"💳 Total Balance: `${CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_v22_engine():
    # V19 Stealth Logic အရ Log တက်စေခြင်း
    print(f"RN1 V22 | PRO STEALTH | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # HTTP/2 Support ဖြင့် Stealth ချိတ်ဆက်ခြင်း 
        with httpx.Client(http2=True, headers=HEADERS, timeout=30.0) as client:
            res = client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=30")
            
            if res.status_code == 200:
                markets = res.json()
                print(f"RN1 Scan | Active Responses: {len(markets)} | Tracking: {len(ACTIVE_TRADES)}")
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for m in markets:
                        executor.submit(check_market_logic, m, client)
            else:
                print(f"⚠️ Access Status: {res.status_code}")
                
    except Exception as e:
        print(f"❌ Engine Error: {e}")

if __name__ == "__main__":
    send_tele("🎯 *RN1 V22: Pro Arbitrage Engine Deployed!*")
    while True:
        run_v22_engine()
        # Polymarket မှ Bot ဟု မသတ်မှတ်စေရန် Random Sleep သုံးသည်
        time.sleep(random.randint(45, 75))

import os
import time
import cloudscraper
import threading
import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CURRENT_BALANCE = 1000.0 
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
MIN_EXIT_PROFIT = 0.02  

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

# --- WebShare Proxy Configuration ---
PROXY_URL = "http://onzoyyph:hed0nyhkyw59@198.105.121.200:6462"
proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# Cloudflare Bypass အတွက် Scraper တည်ဆောက်ခြင်း
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def check_spread_strategy(market):
    global CURRENT_BALANCE, ACTIVE_TRADES
    try:
        question = market.get('question', '')
        market_id = market.get('conditionId')
        tokens = market.get('clobTokenIds', [])
        
        if not tokens or len(tokens) < 2: return
        y_id, n_id = tokens[0], tokens[1]
        
        # ၁။ Entry Check
        if market_id not in ACTIVE_TRADES:
            # Proxy သုံး၍ ဈေးနှုန်းခေါ်ယူခြင်း
            y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=BUY", proxies=proxies, timeout=10).json()
            n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=BUY", proxies=proxies, timeout=10).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            if y_p > 0.01 and n_p > 0.01 and "2023" not in question:
                ACTIVE_TRADES[market_id] = {'y_entry': y_p, 'n_entry': n_p, 'q': question}
                entry_msg = (
                    f"🎯 *LIVE ORDERBOOK ENTRY*\n📌 {question}\n"
                    f"----------------------------\n"
                    f"🟢 Yes Entry: `${y_p:.3f}`\n🔴 No Entry: `${n_p:.3f}`\n"
                    f"💵 Size: `${TRADE_SIZE}` | Bal: `${CURRENT_BALANCE}`"
                )
                send_tele(entry_msg)
                return

        # ၂။ Exit Check
        y_res = scraper.get(f"https://clob.polymarket.com/price?token_id={y_id}&side=SELL", proxies=proxies, timeout=10).json()
        n_res = scraper.get(f"https://clob.polymarket.com/price?token_id={n_id}&side=SELL", proxies=proxies, timeout=10).json()
        y_bid, n_bid = float(y_res.get('price', 0)), float(n_res.get('price', 0))

        if (y_bid + n_bid) > (1.0 + MIN_EXIT_PROFIT):
            net_profit = (TRADE_SIZE * (y_bid + n_bid)) - (TRADE_SIZE * 2) - GAS_BUFFER
            with balance_lock:
                CURRENT_BALANCE += net_profit
                exit_msg = (
                    f"💰 *PROFIT TAKEN*\n📌 {question}\n"
                    f"📥 Entry Sum: `${ACTIVE_TRADES[market_id]['y_entry'] + ACTIVE_TRADES[market_id]['n_entry']:.3f}`\n"
                    f"📤 Exit Sum: `${y_bid + n_bid:.3f}`\n"
                    f"💵 Net: `+${net_profit:.4f}` | Bal: `{CURRENT_BALANCE:.2f}`"
                )
                send_tele(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

def run_scanner():
    # Proxy IP အလုပ်လုပ်ပုံကို စစ်ဆေးခြင်း
    try:
        ip_check = scraper.get("https://api.ipify.org", proxies=proxies, timeout=10).text
        print(f"RN1 Scan | IP: {ip_check} | Bal: ${CURRENT_BALANCE:.2f} | Active: {len(ACTIVE_TRADES)}")
    except:
        print("❌ Proxy Connection Error!")
        return

    try:
        gamma_url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&order=volume24hr"
        res = scraper.get(gamma_url, proxies=proxies, timeout=20).json()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            for m in res:
                if m.get('clobTokenIds'):
                    executor.submit(check_spread_strategy, m)
    except Exception as e:
        print(f"Scanner Error: {e}")

if __name__ == "__main__":
    send_tele("⚡ *RN1 V4: Proxy-Enabled Engine Online!*")
    while True:
        run_scanner()
        time.sleep(20)

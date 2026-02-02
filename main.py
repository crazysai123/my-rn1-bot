import os
import time
import requests
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configs & Telegram ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Bot API Token
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # သင့်ရဲ့ User ID
START_BALANCE = 100.0
TOTAL_BALANCE = 100.0
TRADE_AMOUNT = 0.5
TRADE_COUNT = 0
GAS_FEE_ESTIMATE = 0.001
MIN_PROFIT_GAP = 0.002
PROFIT_MARGIN = 0.001

# --- Reporting & Session ---
daily_trades = 0
daily_profit = 0.0
next_report_time = datetime.now() + timedelta(days=1)
balance_lock = threading.Lock()

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

GREEN, YELLOW, CYAN, RED, RESET = '\033[92m', '\033[93m', '\033[96m', '\033[91m', '\033[0m'

def send_telegram(message):
    if not TELE_TOKEN or not TELE_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except: pass

def check_and_send_report():
    global daily_trades, daily_profit, next_report_time
    if datetime.now() >= next_report_time:
        report = (
            f"📅 *DAILY REPORT*\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 Daily Profit: `${daily_profit:.4f}`\n"
            f"🔄 Total Trades: `{daily_trades}`\n"
            f"💳 Balance: `${TOTAL_BALANCE:.2f}`"
        )
        send_telegram(report)
        daily_trades = 0
        daily_profit = 0.0
        next_report_time = datetime.now() + timedelta(days=1)

def check_market(market, tag):
    global TOTAL_BALANCE, TRADE_COUNT, daily_trades, daily_profit
    try:
        y_url = f"https://clob.polymarket.com/price?token_id={market['tokens'][0]['token_id']}&side=BUY"
        n_url = f"https://clob.polymarket.com/price?token_id={market['tokens'][1]['token_id']}&side=BUY"
        
        y_res = session.get(y_url, timeout=2)
        n_res = session.get(n_url, timeout=2)

        # Rate Limit Alert
        if y_res.status_code == 429:
            send_telegram("⚠️ *API Rate Limit Hit!* Bot is cooling down...")
            return

        y_p = float(y_res.json().get('price', 0))
        n_p = float(n_res.json().get('price', 0))
        total_sum = y_p + n_p

        if 0 < total_sum < (1.0 - PROFIT_MARGIN):
            net_profit = (TRADE_AMOUNT / total_sum) - TRADE_AMOUNT - GAS_FEE_ESTIMATE

            if net_profit >= MIN_PROFIT_GAP:
                with balance_lock:
                    TRADE_COUNT += 1
                    daily_trades += 1
                    daily_profit += net_profit
                    TOTAL_BALANCE += net_profit
                    
                    if TOTAL_BALANCE < (START_BALANCE * 0.5):
                        send_telegram("🚨 *STOP-LOSS!* Balance dropped below 50%. Bot Killed.")
                        os._exit(1)
                    
                    alert = (
                        f"✅ *TRADE SUCCESS #{TRADE_COUNT}*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📊 Market: `{tag}`\n"
                        f"💵 Profit: `+${net_profit:.4f}`\n"
                        f"💳 Balance: `${TOTAL_BALANCE:.2f}`"
                    )
                    send_telegram(alert)
                    print(f"{GREEN}[SUCCESS] Telegram Alert Sent.{RESET}")
    except: pass

def fast_scan():
    check_and_send_report()
    all_targets = []
    try:
        url = "https://clob.polymarket.com/markets?active=true"
        res = session.get(url, timeout=5).json()
        markets = res if isinstance(res, list) else res.get('data', [])
        for m in markets[:40]: all_targets.append((m, "Live"))
    except: pass

    with ThreadPoolExecutor(max_workers=10) as executor:
        for market, tag in all_targets: executor.submit(check_market, market, tag)

if __name__ == "__main__":
    send_telegram("🚀 *RN1 Bot Online!* Starting Polymarket scan...")
    while True:
        fast_scan()
        time.sleep(3)

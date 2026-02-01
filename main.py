import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings
PROFIT_MARGIN = 0.003    # Catch gaps at 0.3%
VIRTUAL_BALANCE = 100.0  
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

total_profit = 0.0

def dry_run_scan():
    global total_profit
    print(f"{CYAN}Verification Scan: Checking Top 50 Markets...{RESET}")
    try:
        url = "https://clob.polymarket.com/markets?active=true"
        headers = {'User-Agent': 'Mozilla/5.0'}
        markets = requests.get(url, headers=headers, timeout=10).json()
        markets = markets if isinstance(markets, list) else markets.get('data', [])
        
        for market in markets[:50]:
            try:
                tokens = market.get('tokens', [])
                y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=3).json().get('price', 0))
                n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=3).json().get('price', 0))
                
                if y_p > 0 and n_p > 0:
                    total_cost = y_p + n_p
                    # ဒီစာကြောင်းက ဈေးနှုန်းတွေကို အမြဲပြပေးမှာပါ
                    print(f"Price Check: {total_cost:.4f} | Target: < {1.0 - PROFIT_MARGIN:.3f}")

                    if total_cost <= (1.0 - PROFIT_MARGIN):
                        earnings = (1.0 - total_cost) * TRADE_AMOUNT
                        total_profit += earnings
                        print(f"\n{GREEN}[!!! TRADE EXECUTED !!!]")
                        print(f"Market: {market.get('question')[:50]}")
                        print(f"Result: Profit ${earnings:.2f} Added to Balance.{RESET}")
            except: continue
            
        print(f"\nCycle Complete. Balance: ${VIRTUAL_BALANCE + total_profit:.2f}")
    except: print("Connection Error...")

def start_bot():
    print(f"{GREEN}Dry Run Verification Started.{RESET}")
    while True:
        dry_run_scan()
        time.sleep(10)

if __name__ == "__main__":
    start_bot()

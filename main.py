import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Updated Strategy Settings
PROFIT_MARGIN = 0.005    # Lowered to 0.5% for more opportunities
VIRTUAL_BALANCE = 100.0  
TRADE_AMOUNT = 10.0      

# Terminal Colors
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

total_profit = 0.0

def get_live_markets():
    url = "https://clob.polymarket.com/markets?active=true"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        all_data = response.json()
        return all_data if isinstance(all_data, list) else all_data.get('data', [])
    except:
        return []

def dry_run_scan():
    global total_profit
    print(f"{CYAN}ONE% Dry Run: Scanning Top 200 Markets (0.5% Margin)...{RESET}")
    markets = get_live_markets()
    
    if not markets:
        print("Waiting for data...")
        return

    # Increased scan count to 200 for wider search
    for market in markets[:200]:
        try:
            tokens = market.get('tokens', [])
            if len(tokens) < 2: continue
            
            y_id = tokens[0]['token_id']
            n_id = tokens[1]['token_id']
            
            y_res = requests.get(f"https://clob.polymarket.com/price?token_id={y_id}", timeout=5).json()
            n_res = requests.get(f"https://clob.polymarket.com/price?token_id={n_id}", timeout=5).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            print(".", end="", flush=True)

            if y_p > 0 and n_p > 0:
                total_cost = y_p + n_p
                # Checking for 0.5% profit gap
                if total_cost <= (1.0 - PROFIT_MARGIN):
                    profit_per_share = 1.0 - total_cost
                    earnings = profit_per_share * TRADE_AMOUNT
                    total_profit += earnings
                    
                    print(f"\n{GREEN}[VIRTUAL TRADE EXECUTED]")
                    print(f"Market: {market.get('question')}")
                    print(f"Price: {total_cost:.3f} | Profit: ${earnings:.2f}")
                    print(f"Wallet Balance: ${VIRTUAL_BALANCE + total_profit:.2f}{RESET}")
        except:
            continue
    print(f"\nScan cycle done. Current Profit: ${total_profit:.2f}")

def start_bot():
    print(f"{GREEN}ONE% Strategy: Dry Run Mode (Aggressive) Active.{RESET}")
    print(f"Starting Virtual Balance: ${VIRTUAL_BALANCE}")
    while True:
        dry_run_scan()
        print("-" * 30)
        time.sleep(10) # Frequency slightly increased

if __name__ == "__main__":
    start_bot()

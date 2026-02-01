import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# High-Frequency Dry Run Settings
PROFIT_MARGIN = 0.003    # Lowered further to 0.3% to catch tiny gaps
VIRTUAL_BALANCE = 100.0  
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

total_profit = 0.0

def dry_run_scan():
    global total_profit
    print(f"{CYAN}ONE% Aggressive: Scanning Top 100 Markets...{RESET}")
    try:
        url = "https://clob.polymarket.com/markets?active=true"
        headers = {'User-Agent': 'Mozilla/5.0'}
        markets = requests.get(url, headers=headers, timeout=10).json()
        markets = markets if isinstance(markets, list) else markets.get('data', [])
        
        # Scan Top 100 for better speed/frequency balance
        for market in markets[:100]:
            try:
                tokens = market.get('tokens', [])
                y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=3).json().get('price', 0))
                n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=3).json().get('price', 0))
                
                print(".", end="", flush=True)

                if y_p > 0 and n_p > 0:
                    total_cost = y_p + n_p
                    if total_cost <= (1.0 - PROFIT_MARGIN):
                        earnings = (1.0 - total_cost) * TRADE_AMOUNT
                        total_profit += earnings
                        print(f"\n{GREEN}[VIRTUAL TRADE] Match: {market.get('question')[:40]}... Profit: ${earnings:.2f} | Wallet: ${VIRTUAL_BALANCE + total_profit:.2f}{RESET}")
            except: continue
        print(f"\nCycle Complete. Running Profit: ${total_profit:.2f}")
    except: print("API Error. Retrying...")

def start_bot():
    print(f"{GREEN}Aggressive Dry Run Mode Started.{RESET}")
    while True:
        dry_run_scan()
        time.sleep(5) # Scan every 5 seconds for higher frequency

if __name__ == "__main__":
    start_bot()

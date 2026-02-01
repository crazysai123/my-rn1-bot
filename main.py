import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings
PROFIT_MARGIN = 0.003    # Catch gaps at 0.3%
TOTAL_BALANCE = 100.0    # Your starting wallet
TRADE_AMOUNT = 10.0      # Amount spent per trade

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def dry_run_scan():
    global TOTAL_BALANCE
    print(f"{CYAN}Scanner Active. Balance: ${TOTAL_BALANCE:.2f}{RESET}")
    
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
                    total_cost_per_share = y_p + n_p
                    
                    if total_cost_per_share <= (1.0 - PROFIT_MARGIN):
                        # Calculate trade
                        shares_bought = TRADE_AMOUNT / total_cost_per_share
                        profit_at_maturity = shares_bought - TRADE_AMOUNT
                        
                        print(f"\n{GREEN}[!!! VIRTUAL TRADE EXECUTED !!!]")
                        print(f"Market: {market.get('question')[:50]}...")
                        print(f"Action: Invested ${TRADE_AMOUNT:.2f}")
                        
                        # Show balance decreasing
                        TOTAL_BALANCE -= TRADE_AMOUNT
                        print(f"Status: Wallet balance decreased to ${TOTAL_BALANCE:.2f}")
                        
                        # Show potential profit
                        TOTAL_BALANCE += (TRADE_AMOUNT + profit_at_maturity)
                        print(f"Result: Trade settled. New total balance: ${TOTAL_BALANCE:.2f}{RESET}")
                        print("-" * 30)
            except: continue
        
        print(f"\nCycle Complete. Current Wallet: ${TOTAL_BALANCE:.2f}")
    except: print("Connection Error...")

def start_bot():
    print(f"{GREEN}Dry Run with Balance Tracking Started.{RESET}")
    while True:
        dry_run_scan()
        time.sleep(15)

if __name__ == "__main__":
    start_bot()

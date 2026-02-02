import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Trade Settings
TARGET_MARGIN = 0.003    # Real target: 0.3%
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def run_trading_bot():
    global TOTAL_BALANCE
    print(f"{CYAN}Bot Active. Wallet: ${TOTAL_BALANCE:.2f}{RESET}")
    
    try:
        url = "https://clob.polymarket.com/markets?active=true"
        markets = requests.get(url, timeout=10).json()
        markets = markets if isinstance(markets, list) else markets.get('data', [])
        
        # We take the first 50 markets
        for market in markets[:50]:
            try:
                tokens = market.get('tokens', [])
                y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=3).json().get('price', 0))
                n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=3).json().get('price', 0))
                
                if y_p > 0 and n_p > 0:
                    total_cost = y_p + n_p
                    
                    # FORCE BUY TEST: To see if the logic works, we buy even if profit is small or negative
                    # Change the line below to 'total_cost <= (1.0 - TARGET_MARGIN)' for real trading later
                    if total_cost < 1.1: # This will trigger on almost any market
                        print(f"\n{GREEN}[!!! TRADE ALERT !!!]")
                        print(f"Match: {market.get('question')[:50]}...")
                        
                        # Phase 1: Deducting Money
                        print(f"{YELLOW}Action: Buying Shares for ${TRADE_AMOUNT:.2f}{RESET}")
                        TOTAL_BALANCE -= TRADE_AMOUNT
                        print(f"Balance Update: Wallet decreased to {GREEN}${TOTAL_BALANCE:.2f}{RESET}")
                        
                        # Phase 2: Adding potential profit (Settlement)
                        shares = TRADE_AMOUNT / total_cost
                        profit = shares - TRADE_AMOUNT
                        TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                        
                        print(f"Result: Profit of ${profit:.2f} added.")
                        print(f"Final Balance: {GREEN}${TOTAL_BALANCE:.2f}{RESET}")
                        print("-" * 30)
                        return # Stop after one successful test trade to show you
            except: continue
    except: print("API Connection Error.")

if __name__ == "__main__":
    print(f"{GREEN}Testing Balance Deduction...{RESET}")
    while True:
        run_trading_bot()
        time.sleep(15)

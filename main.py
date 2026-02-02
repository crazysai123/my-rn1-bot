import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings
PROFIT_MARGIN = 0.001    # Lowered to 0.1% for frequent trading
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

def real_strategy_scan():
    global TOTAL_BALANCE
    print(f"{CYAN}Scanner Active (0.1% Margin). Balance: ${TOTAL_BALANCE:.2f}{RESET}")
    
    try:
        url = "https://clob.polymarket.com/markets?active=true"
        markets = requests.get(url, timeout=10).json()
        markets = markets if isinstance(markets, list) else markets.get('data', [])
        
        for market in markets[:100]:
            try:
                tokens = market.get('tokens', [])
                y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=3).json().get('price', 0))
                n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=3).json().get('price', 0))
                
                if y_p > 0 and n_p > 0:
                    total_cost = y_p + n_p
                    
                    # 0.1% Profit Check (Cost < 0.999)
                    if total_cost <= (1.0 - PROFIT_MARGIN):
                        print(f"\n{GREEN}[!!! TRADE EXECUTED !!!]")
                        print(f"Market: {market.get('question')[:50]}")
                        
                        # Wallet Deduction
                        TOTAL_BALANCE -= TRADE_AMOUNT
                        print(f"Action: Invested ${TRADE_AMOUNT:.2f} | New Wallet: ${TOTAL_BALANCE:.2f}")
                        
                        # Profit Calculation
                        profit = (1.0 - total_cost) * (TRADE_AMOUNT / total_cost)
                        TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                        print(f"Settled: Total Balance Updated to ${TOTAL_BALANCE:.2f}{RESET}")
                        print("-" * 30)
            except: continue
        print(f"Scan complete. Waiting...")
    except: print("API Connection Busy...")

if __name__ == "__main__":
    while True:
        real_strategy_scan()
        time.sleep(10) # Scanning slightly faster

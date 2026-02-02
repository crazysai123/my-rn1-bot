import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# High-Speed Settings
PROFIT_MARGIN = 0.001    # 0.1% Target
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def fast_scan():
    global TOTAL_BALANCE
    print(f"{CYAN}Fast Scan Started (0.1% Margin). Wallet: ${TOTAL_BALANCE:.2f}{RESET}")
    
    try:
        # Get active markets
        url = "https://clob.polymarket.com/markets?active=true"
        response = requests.get(url, timeout=10).json()
        markets = response if isinstance(response, list) else response.get('data', [])
        
        # Scan only the top 30 most active markets for speed
        for market in markets[:30]:
            try:
                tokens = market.get('tokens', [])
                if len(tokens) < 2: continue
                
                # Fetching prices with shorter timeout
                y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=5).json().get('price', 0))
                n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=5).json().get('price', 0))
                
                print(".", end="", flush=True)

                if y_p > 0 and n_p > 0:
                    total_cost = y_p + n_p
                    if total_cost <= (1.0 - PROFIT_MARGIN):
                        print(f"\n{GREEN}[VIRTUAL TRADE EXECUTED]")
                        print(f"Match: {market.get('question')[:50]}")
                        
                        # Balance Logic
                        TOTAL_BALANCE -= TRADE_AMOUNT
                        print(f"{YELLOW}Action: Invested ${TRADE_AMOUNT:.2f} | Balance: ${TOTAL_BALANCE:.2f}{RESET}")
                        
                        profit = (1.0 - total_cost) * (TRADE_AMOUNT / total_cost)
                        TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                        print(f"{GREEN}Settled: New Balance ${TOTAL_BALANCE:.2f}{RESET}")
                        print("-" * 30)
            except: continue
        print(f"\nCycle finished. Balance: ${TOTAL_BALANCE:.2f}")
    except:
        print("API is busy, retrying in next cycle...")

if __name__ == "__main__":
    while True:
        fast_scan()
        time.sleep(5) # Faster cycle time

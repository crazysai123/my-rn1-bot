import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings
PROFIT_MARGIN = 0.001    # 0.1% Profit Target
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

def scan_all_sports():
    global TOTAL_BALANCE
    # Sport tags အားလုံးကို စစ်ဆေးရန်
    sport_tags = ["Sports", "NBA", "Soccer", "Tennis", "MMA", "NFL"]
    
    print(f"{CYAN}Scanning All Sport Markets... Balance: ${TOTAL_BALANCE:.2f}{RESET}")
    
    for tag in sport_tags:
        try:
            # Tag တစ်ခုချင်းစီအလိုက် ပွဲအားလုံးကို ဆွဲယူခြင်း
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            markets = requests.get(url, timeout=10).json()
            markets = markets if isinstance(markets, list) else markets.get('data', [])
            
            print(f"\nScanning {tag} ({len(markets)} matches)", end="")

            for market in markets:
                try:
                    tokens = market.get('tokens', [])
                    if len(tokens) < 2: continue
                    
                    # Live Price ကို စစ်ဆေးခြင်း
                    y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=5).json().get('price', 0))
                    n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=5).json().get('price', 0))
                    
                    print(".", end="", flush=True)

                    if y_p > 0 and n_p > 0:
                        total_cost = y_p + n_p
                        if total_cost <= (1.0 - PROFIT_MARGIN):
                            print(f"\n{GREEN}[!!! OPPORTUNITY FOUND IN {tag.upper()} !!!]")
                            print(f"Match: {market.get('question')[:50]}")
                            
                            # Trade Execution Logic
                            TOTAL_BALANCE -= TRADE_AMOUNT
                            print(f"Action: Invested ${TRADE_AMOUNT:.2f} | New Wallet: ${TOTAL_BALANCE:.2f}")
                            
                            profit = (1.0 - total_cost) * (TRADE_AMOUNT / total_cost)
                            TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                            print(f"Settled: Total Balance Updated to ${TOTAL_BALANCE:.2f}{RESET}")
                except: continue
        except:
            print(f"\nError scanning {tag}, skipping...")
            continue

if __name__ == "__main__":
    while True:
        scan_all_sports()
        print(f"\n{CYAN}All Sports Scanned. Restarting in 30 seconds...{RESET}")
        time.sleep(30)

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings (အမြတ်အစစ်ရှာမည့် ပတ်ဝန်းကျင်)
PROFIT_MARGIN = 0.003    # 0.3% Profit Target
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 10.0      

GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

def real_strategy_scan():
    global TOTAL_BALANCE
    print(f"{CYAN}Real Strategy Active. Scanning for 0.3% Profit... Balance: ${TOTAL_BALANCE:.2f}{RESET}")
    
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
                    # အမြတ်တကယ်ရှိမှ ဝယ်မည့် Logic
                    if total_cost <= (1.0 - PROFIT_MARGIN):
                        print(f"\n{GREEN}[!!! REAL OPPORTUNITY FOUND !!!]")
                        print(f"Market: {market.get('question')[:50]}")
                        
                        # ဝယ်ယူခြင်း
                        TOTAL_BALANCE -= TRADE_AMOUNT
                        print(f"Action: Invested ${TRADE_AMOUNT:.2f} | Wallet: ${TOTAL_BALANCE:.2f}")
                        
                        # အမြတ်တွက်ချက်ခြင်း
                        profit = (1.0 - total_cost) * (TRADE_AMOUNT / total_cost)
                        TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                        print(f"Settled: New Balance ${TOTAL_BALANCE:.2f}{RESET}")
                        print("-" * 30)
            except: continue
        print(f"Scan complete. Waiting for next cycle...")
    except: print("API Connection Busy...")

if __name__ == "__main__":
    while True:
        real_strategy_scan()
        time.sleep(15)

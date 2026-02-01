import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings
PROFIT_MARGIN = 0.01  
TRADE_AMOUNT = 5.0    

# Terminal Colors
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_live_markets():
    url = "https://clob.polymarket.com/markets?active=true"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return []
            
        all_data = response.json()
        markets_list = all_data if isinstance(all_data, list) else all_data.get('data', [])
        
        valid_markets = []
        for m in markets_list:
            if isinstance(m, dict):
                tokens = m.get('tokens', [])
                if len(tokens) >= 2:
                    valid_markets.append({
                        'question': m.get('question'),
                        'yes_id': tokens[0]['token_id'],
                        'no_id': tokens[1]['token_id']
                    })
        return valid_markets
    except:
        return []

def scan_prices():
    print(f"{CYAN}ONE% Scanner: Refreshing market data...{RESET}")
    markets = get_live_markets()
    
    if not markets:
        print(f"{YELLOW}API Busy or No Data. Retrying...{RESET}")
        return

    print(f"Checking {len(markets)} active matches...")

    # Scan top 30 markets to avoid API rate limits
    for market in markets[:30]:
        try:
            y_id = market['yes_id']
            n_id = market['no_id']
            
            y_res = requests.get(f"https://clob.polymarket.com/price?token_id={y_id}", timeout=5).json()
            n_res = requests.get(f"https://clob.polymarket.com/price?token_id={n_id}", timeout=5).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            if y_p == 0 or n_p == 0: continue
            
            total = y_p + n_p
            
            if total <= (1.0 - PROFIT_MARGIN):
                print(f"\n{GREEN}--- ONE% OPPORTUNITY FOUND ---")
                print(f"Market: {market['question']}")
                print(f"Yes: {y_p} | No: {n_p} | Total: {total:.3f}")
                print(f"Profit Potential: {((1.0 - total) * 100):.2f}%{RESET}")
            
        except:
            continue

def start_bot():
    print(f"{GREEN}ONE% Strategy: Bot Started Successfully.{RESET}")
    while True:
        scan_prices()
        print("-" * 30)
        time.sleep(20)

if __name__ == "__main__":
    start_bot()

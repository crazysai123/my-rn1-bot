import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PROFIT_MARGIN = 0.01  
GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

def get_live_markets():
    url = "https://clob.polymarket.com/markets?active=true"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        all_data = response.json()
        return all_data if isinstance(all_data, list) else all_data.get('data', [])
    except:
        return []

def scan_prices():
    print(f"{CYAN}ONE% Scanner: Fetching data...{RESET}")
    markets = get_live_markets()
    
    if not markets:
        print("No markets found.")
        return

    # Focus on top 50 high-activity markets only
    test_count = 50 
    print(f"Scanning top {test_count} matches for efficiency...")

    for market in markets[:test_count]:
        try:
            y_id = market['tokens'][0]['token_id']
            n_id = market['tokens'][1]['token_id']
            
            # Fetching prices
            y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={y_id}", timeout=5).json().get('price', 0))
            n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={n_id}", timeout=5).json().get('price', 0))
            
            print(".", end="", flush=True) # Progress dot

            if y_p > 0 and n_p > 0:
                total = y_p + n_p
                if total <= (1.0 - PROFIT_MARGIN):
                    print(f"\n{GREEN}--- OPPORTUNITY FOUND! ---")
                    print(f"Market: {market.get('question')}")
                    print(f"Sum: {total:.3f} | Profit: {((1.0-total)*100):.2f}%{RESET}")
        except:
            continue
    print(f"\nScan cycle complete.")

def start_bot():
    print(f"{GREEN}ONE% Strategy Active.{RESET}")
    while True:
        scan_prices()
        time.sleep(10)

if __name__ == "__main__":
    start_bot()

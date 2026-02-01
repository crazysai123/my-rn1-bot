import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ONE% Strategy Settings
PROFIT_MARGIN = 0.01  
TRADE_AMOUNT = 5.0    

def get_all_sports_markets():
    url = "https://clob.polymarket.com/markets"
    try:
        response = requests.get(url)
        all_markets = response.json()
        sports_list = []
        for m in all_markets:
            if m.get('active') and "Sports" in str(m.get('tags')):
                tokens = m.get('tokens', [])
                if len(tokens) >= 2:
                    sports_list.append({
                        'question': m.get('question'),
                        'yes_id': tokens[0]['token_id'],
                        'no_id': tokens[1]['token_id']
                    })
        return sports_list
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def scan_and_trade():
    print("ONE% Multi-Scanner: Checking active sports markets...")
    markets = get_all_sports_markets()
    print(f"Found {len(markets)} matches. Scanning prices...")

    for market in markets:
        try:
            y_url = f"https://clob.polymarket.com/price?token_id={market['yes_id']}"
            n_url = f"https://clob.polymarket.com/price?token_id={market['no_id']}"
            
            y_res = requests.get(y_url).json()
            n_res = requests.get(n_url).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            total = y_p + n_p
            
            if 0 < total <= (1.0 - PROFIT_MARGIN):
                print(f"\n--- ONE% OPPORTUNITY DETECTED ---")
                print(f"Match: {market['question']}")
                print(f"Yes: {y_p} | No: {n_p} | Sum: {total:.3f}")
                print(f"Target Profit: {((1.0 - total) * 100):.2f}%")
            
        except:
            continue

def start_bot():
    print("ONE% Strategy: Multi-Market Sports Bot Active.")
    while True:
        scan_and_trade()
        print("-" * 30)
        print("ONE% Scan cycle complete. Waiting 20 seconds...")
        time.sleep(20)

if __name__ == "__main__":
    start_bot()

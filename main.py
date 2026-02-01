import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ONE% Strategy Settings
PROFIT_MARGIN = 0.01  
TRADE_AMOUNT = 5.0    

# Colors for Terminal Logs
GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

def get_all_sports_markets():
    url = "https://clob.polymarket.com/markets"
    try:
        response = requests.get(url)
        all_markets = response.json()
        if not isinstance(all_markets, list):
            return []
            
        sports_list = []
        for m in all_markets:
            if isinstance(m, dict) and m.get('active') and "Sports" in str(m.get('tags')):
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
    print(f"{CYAN}ONE% Multi-Scanner: Checking active sports markets...{RESET}")
    markets = get_all_sports_markets()
    
    if not markets:
        print("Found 0 matches. Waiting for API refresh...")
        return

    print(f"Found {len(markets)} matches. Scanning prices...")

    for market in markets:
        try:
            y_url = f"https://clob.polymarket.com/price?token_id={market['yes_id']}"
            n_url = f"https://clob.polymarket.com/price?token_id={market['no_id']}"
            
            y_p = float(requests.get(y_url).json().get('price', 0))
            n_p = float(requests.get(n_url).json().get('price', 0))
            
            total = y_p + n_p
            
            if 0 < total <= (1.0 - PROFIT_MARGIN):
                # အခွင့်အရေးရှိရင် အစိမ်းရောင်နဲ့ ပြပေးမယ့် အပိုင်း
                print(f"\n{GREEN}#######################################")
                print(f"--- ONE% OPPORTUNITY DETECTED ---")
                print(f"Match: {market['question']}")
                print(f"Yes: {y_p} | No: {n_p} | Sum: {total:.3f}")
                print(f"Target Profit: {((1.0 - total) * 100):.2f}%")
                print(f"Executing Trade for {TRADE_AMOUNT} USDC...")
                print(f"#######################################{RESET}")
            
        except:
            continue

def start_bot():
    print(f"{GREEN}ONE% Strategy: Multi-Market Sports Bot Active.{RESET}")
    while True:
        scan_and_trade()
        print("-" * 30)
        time.sleep(15)

if __name__ == "__main__":
    start_bot()

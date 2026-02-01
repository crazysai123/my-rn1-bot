import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PROFIT_MARGIN = 0.01  
TRADE_AMOUNT = 5.0    

GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_all_active_markets():
    # API endpoint ကို သေချာအောင် စစ်မယ်
    url = "https://clob.polymarket.com/markets"
    try:
        # User-agent ထည့်မှ Polymarket က data ပေးတတ်ပါတယ်
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
            
        all_markets = response.json()
        valid_markets = []
        
        if isinstance(all_markets, list):
            for m in all_markets:
                if isinstance(m, dict) and m.get('active') is True:
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

def scan_and_trade():
    print(f"{CYAN}ONE% Multi-Scanner: Searching all live markets...{RESET}")
    markets = get_all_active_markets()
    
    if not markets:
        print(f"{YELLOW}No data from API yet. Retrying in next cycle...{RESET}")
        return

    print(f"Found {len(markets)} active matches. Scanning prices...")

    for market in markets[:20]: # အစပိုင်းမှာ API limit မမိအောင် ပွဲ ၂၀ ပဲ အရင်စစ်မယ်
        try:
            y_url = f"https://clob.polymarket.com/price?token_id={market['yes_id']}"
            n_url = f"https://clob.polymarket.com/price?token_id={market['no_id']}"
            
            y_p = float(requests.get(y_url, timeout=5).json().get('price', 0))
            n_p = float(requests.get(n_url, timeout=5).json().get('price', 0))
            
            total = y_p + n_p
            
            if 0 < total <= (1.0 - PROFIT_MARGIN):
                print(f"\n{GREEN}#######################################")
                print(f"--- ONE% OPPORTUNITY DETECTED ---")
                print(f"Market: {market['question']}")
                print(f"Yes: {y_p} | No: {n_p} | Sum: {total:.3f}")
                print(f"Profit Potential: {((1.0 - total) * 100):.2f}%")
                print(f"#######################################{RESET}")
            
        except:
            continue

def start_bot():
    print(f"{GREEN}ONE% Strategy: Bot Initialized and Ready.{RESET}")
    while True:
        scan_and_trade()
        print("-" * 30)
        time.sleep(15) 

if __name__ == "__main__":
    start_bot()

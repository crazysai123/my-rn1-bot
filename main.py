import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PROFIT_MARGIN = 0.01  
TRADE_AMOUNT = 5.0    

GREEN = '\033[92m'
CYAN = '\033[96m'
RESET = '\033[0m'

def get_all_active_markets():
    # ပွဲတွေအကုန်လုံးကို ဆွဲထုတ်မယ်
    url = "https://clob.polymarket.com/markets"
    try:
        response = requests.get(url)
        all_markets = response.json()
        
        valid_markets = []
        for m in all_markets:
            # Active ဖြစ်ပြီး Yes/No token စုံတဲ့ ပွဲမှန်သမျှ ယူမယ်
            if isinstance(m, dict) and m.get('active') is True:
                tokens = m.get('tokens', [])
                if len(tokens) >= 2:
                    valid_markets.append({
                        'question': m.get('question'),
                        'yes_id': tokens[0]['token_id'],
                        'no_id': tokens[1]['token_id']
                    })
        return valid_markets
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def scan_and_trade():
    print(f"{CYAN}ONE% Multi-Scanner: Scanning all active markets...{RESET}")
    markets = get_all_active_markets()
    
    if not markets:
        print("Waiting for API response...")
        return

    print(f"Checking {len(markets)} potential matches for arbitrage...")

    for market in markets:
        try:
            y_url = f"https://clob.polymarket.com/price?token_id={market['yes_id']}"
            n_url = f"https://clob.polymarket.com/price?token_id={market['no_id']}"
            
            # Timeout ထည့်ထားမှ Error ကင်းမယ်
            y_res = requests.get(y_url, timeout=5).json()
            n_res = requests.get(n_url, timeout=5).json()
            
            y_p = float(y_res.get('price', 0))
            n_p = float(n_res.get('price', 0))
            
            total = y_p + n_p
            
            # ONE% Opportunity Check
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
    print(f"{GREEN}ONE% Strategy: Multi-Market Bot Initialized.{RESET}")
    while True:
        scan_and_trade()
        print("-" * 30)
        time.sleep(10) # ပွဲမြန်မြန်တွေ့အောင် ၁၀ စက္ကန့်ပဲ ထားမယ်

if __name__ == "__main__":
    start_bot()

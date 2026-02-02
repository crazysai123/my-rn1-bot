import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Wallet Settings
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 50.0      # ဝယ်လိုက်ရင် $50 တစ်ခါတည်း လျော့သွားတာ မြင်ရအောင် $50 ထားလိုက်မယ်

GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def force_test_trade():
    global TOTAL_BALANCE
    print(f"{CYAN}Testing Instant Trade Logic... Balance: ${TOTAL_BALANCE:.2f}{RESET}")
    
    try:
        # Polymarket API ကနေ Active ဖြစ်နေတဲ့ ပွဲတွေကို ယူမယ်
        url = "https://clob.polymarket.com/markets?active=true"
        response = requests.get(url, timeout=10).json()
        markets = response if isinstance(response, list) else response.get('data', [])
        
        if not markets:
            print("No markets found to trade.")
            return

        # ပထမဆုံးတွေ့တဲ့ ပွဲကိုပဲ ဈေးမရွေးဘဲ ဝယ်ပစ်မယ်
        market = markets[0]
        question = market.get('question', 'Unknown Market')
        
        print(f"\n{YELLOW}Step 1: Found Market -> {question[:50]}...{RESET}")
        
        # Balance လျော့သွားတာကို အရင်ပြမယ်
        print(f"{GREEN}[EXECUTION] Buying Shares for ${TRADE_AMOUNT:.2f}...{RESET}")
        TOTAL_BALANCE -= TRADE_AMOUNT
        print(f"WALLET UPDATE: Balance decreased to {YELLOW}${TOTAL_BALANCE:.2f}{RESET}")
        
        # ခဏစောင့်ပြီး အမြတ်ပြန်ပေါင်းပြမယ်
        time.sleep(2)
        simulated_profit = 1.50 # စမ်းသပ်ဖို့အတွက် အမြတ် $1.50 ရတယ်လို့ ထားလိုက်မယ်
        TOTAL_BALANCE += (TRADE_AMOUNT + simulated_profit)
        
        print(f"{GREEN}[SUCCESS] Trade Settled. Profit: ${simulated_profit:.2f}")
        print(f"NEW BALANCE: ${TOTAL_BALANCE:.2f}{RESET}\n")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    print(f"{GREEN}Force-Trade Script Started.{RESET}")
    while True:
        force_test_trade()
        print("Waiting 10 seconds for next test...")
        time.sleep(10)

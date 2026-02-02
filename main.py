import os
import time
import requests
import traceback
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Config အပိုင်း (Action အားလုံး ပါဝင်သည်) ---
PROFIT_MARGIN = 0.0001
TOTAL_BALANCE = 100.0
TRADE_AMOUNT = 0.5
TRADE_COUNT = 0

GREEN, YELLOW, CYAN, RED, RESET = '\033[92m', '\033[93m', '\033[96m', '\033[91m', '\033[0m'
MARKET_TAGS = ["Sports", "NBA", "Soccer", "Gaming", "Crypto", "Politics"]

def check_market(market, tag):
    global TOTAL_BALANCE, TRADE_COUNT
    try:
        tokens = market.get('tokens', [])
        if len(tokens) < 2:
            return
        
        token_id = tokens[0]['token_id']
        ob_url = f"https://clob.polymarket.com/book?token_id={token_id}"
        
        response = requests.get(ob_url, timeout=3)
        if response.status_code != 200:
            print(f"{RED}[API ERROR] Status: {response.status_code}{RESET}")
            return

        book = response.json()
        bids = book.get('bids', [])
        if not bids:
            return

        y_p = float(bids[0].get('price', 0))
        n_p = 1.0 - y_p # Arbitrage Logic

        # --- Auto Trade & Profit Action ---
        if y_p > 0 and (y_p + n_p) <= (1.0 - PROFIT_MARGIN):
            TRADE_COUNT += 1
            # အမြတ်တွက်ချက်ခြင်း
            shares = TRADE_AMOUNT / (y_p + n_p)
            profit = shares - TRADE_AMOUNT
            TOTAL_BALANCE += profit
            
            print(f"{GREEN}[TRADE #{TRADE_COUNT}] {tag} Found Success!{RESET}")
            print(f"{YELLOW}   Profit Added. Wallet: ${TOTAL_BALANCE:.2f}{RESET}")

    except Exception as e:
        print(f"{RED}[ERROR] {str(e)}{RESET}")

def aggressive_scan():
    print(f"\n{CYAN}--- RN1 Aggressive Mode | Trades: {TRADE_COUNT} | Balance: ${TOTAL_BALANCE:.2f} ---{RESET}")
    
    all_markets = []
    for tag in MARKET_TAGS:
        try:
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            res = requests.get(url, timeout=5)
            if res.status_code == 429:
                print(f"{RED}[LIMIT] API Overload. Waiting...{RESET}")
                time.sleep(5)
                continue

            data = res.json()
            markets = data if isinstance(data, list) else data.get('data', [])
            for m in markets[:12]: # ပွဲများကို တပြိုင်နက်စစ်ရန် စုစည်းခြင်း
                all_markets.append((m, tag))
        except Exception as e:
            print(f"{RED}[SCAN ERROR] {str(e)}{RESET}")

    # Thread 8 ခုသုံးပြီး တပြိုင်နက် စစ်ဆေးခြင်း
    with ThreadPoolExecutor(max_workers=8) as executor:
        for market, tag in all_markets:
            executor.submit(check_market, market, tag)

if __name__ == "__main__":
    while True:
        try:
            aggressive_scan()
            time.sleep(3) # စောင့်ဆိုင်းချိန်
        except Exception as main_e:
            print(f"{RED}[CRITICAL ERROR] {str(main_e)}{RESET}")
            time.sleep(5)

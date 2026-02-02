import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations (Action အားလုံး ပါဝင်သည်) ---
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
        if len(tokens) < 2: return
        
        # 404 Error မတက်စေရန် ပိုမိုသေချာသော Price API သို့ ပြန်ပြောင်းသည်
        token_id = tokens[0]['token_id']
        price_url = f"https://clob.polymarket.com/price?token_id={token_id}&side=BUY"
        
        response = requests.get(price_url, timeout=5)
        
        if response.status_code == 200:
            y_p = float(response.json().get('price', 0))
            n_p = 1.0 - y_p # Arbitrage Logic

            # --- Auto Trade Action ---
            if y_p > 0 and (y_p + n_p) <= (1.0 - PROFIT_MARGIN):
                TRADE_COUNT += 1
                shares = TRADE_AMOUNT / (y_p + n_p)
                profit = shares - TRADE_AMOUNT
                TOTAL_BALANCE += profit
                
                print(f"{GREEN}[TRADE #{TRADE_COUNT}] {tag} Success!{RESET}")
                print(f"{YELLOW}   New Balance: ${TOTAL_BALANCE:.2f}{RESET}")
        elif response.status_code != 404: # 404 မဟုတ်သော အခြား Error များကိုသာ ပြရန်
             print(f"{RED}[API ERROR] {response.status_code}{RESET}")

    except Exception:
        pass # မလိုအပ်သော Error log များ လျှော့ချရန်

def aggressive_scan():
    print(f"\n{CYAN}--- RN1 Aggressive Mode | Trades: {TRADE_COUNT} | Balance: ${TOTAL_BALANCE:.2f} ---{RESET}")
    
    all_markets = []
    for tag in MARKET_TAGS:
        try:
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                markets = data if isinstance(data, list) else data.get('data', [])
                for m in markets[:10]:
                    all_markets.append((m, tag))
        except: continue

    # တပြိုင်နက် စစ်ဆေးခြင်း (Concurrent)
    with ThreadPoolExecutor(max_workers=5) as executor:
        for market, tag in all_markets:
            executor.submit(check_market, market, tag)

if __name__ == "__main__":
    while True:
        aggressive_scan()
        time.sleep(5) # Rate Limit မမိစေရန် ၅ စက္ကန့် နားသည်

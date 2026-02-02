import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# Aggressive Settings
import os
import time
import requests
import traceback # Error အသေးစိတ်ကြည့်ရန်
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

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
        
        # Orderbook API ကိုသုံးခြင်းက ဈေးနှုန်းပိုမှန်ပြီး မြန်စေသည် (Polling Optimization)
        # Polymarket CLOB Orderbook API
        token_id = tokens[0]['token_id']
        ob_url = f"https://clob.polymarket.com/book?token_id={token_id}"
        
        response = requests.get(ob_url, timeout=3)
        
        # API Blocking သို့မဟုတ် Error ရှိမရှိ စစ်ဆေးခြင်း (Error Logging)
        if response.status_code != 200:
            print(f"{RED}[API ERROR] Status: {response.status_code} on Tag: {tag}{RESET}")
            return

        book = response.json()
        # Best Bid/Ask ကို ယူခြင်း
        y_p = float(book.get('bids', [{}])[0].get('price', 0))
        n_p = 1.0 - y_p # Arbitrage Logic အရ Yes ဈေးကိုကြည့်ပြီး No ဈေးကို တွက်ချက်ခြင်း

        if y_p > 0 and (y_p + n_p) <= (1.0 - PROFIT_MARGIN):
            TRADE_COUNT += 1
            profit = (TRADE_AMOUNT / (y_p + n_p)) - TRADE_AMOUNT
            TOTAL_BALANCE += profit
            print(f"{GREEN}[TRADE #{TRADE_COUNT}] {tag} Success! New Balance: ${TOTAL_BALANCE:.2f}{RESET}")

    except Exception as e:
        # Error ဖြစ်ခဲ့ရင် pass မလုပ်ဘဲ ဘာကြောင့်ဖြစ်လဲဆိုတာ ပြပေးမယ်
        print(f"{RED}[LOG ERROR] {str(e)}{RESET}")
        # traceback.print_exc() # လိုအပ်လျှင် ဤစာကြောင်းကိုဖွင့်ပြီး Error အပြည့်အစုံကြည့်နိုင်သည်

def aggressive_scan():
    print(f"\n{CYAN}--- RN1 Aggressive Cycle | Trades: {TRADE_COUNT} | Wallet: ${TOTAL_BALANCE:.2f} ---{RESET}")
    
    all_markets = []
    for tag in MARKET_TAGS:
        try:
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            res = requests.get(url, timeout=5)
            if res.status_code == 429:
                print(f"{RED}[WARNING] API Rate Limited. Sleeping for 10s...{RESET}")
                time.sleep(10)
                return

            markets = res.json()
            markets = markets if isinstance(markets, list) else markets.get('data', [])
            for m in markets[:12]:
                all_markets.append((m, tag))
        except Exception as e:
            print(f"{RED}[SCAN ERROR] {tag}: {str(e)}{RESET}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        for market, tag in all_markets:
            executor.submit(check_market, market, tag)

if __name__ == "__main__":
    while True:
        aggressive_scan()
        time.sleep(3)
 = 0.0001
TOTAL_BALANCE = 100.0
TRADE_AMOUNT = 0.5
TRADE_COUNT = 0

GREEN, YELLOW, CYAN, RESET = '\033[92m', '\033[93m', '\033[96m', '\033[0m'
MARKET_TAGS = ["Sports", "NBA", "Soccer", "Gaming", "Crypto", "Politics"]

def check_market(market, tag):
    global TOTAL_BALANCE, TRADE_COUNT
    try:
        tokens = market.get('tokens', [])
        if len(tokens) < 2: return
        
        # Prices ကို Concurrent ဖြစ်အောင် Timeout တိုတိုနဲ့ ဆွဲယူမယ်
        y_url = f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}&side=BUY"
        n_url = f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}&side=BUY"
        
        y_p = float(requests.get(y_url, timeout=2).json().get('price', 0))
        n_p = float(requests.get(n_url, timeout=2).json().get('price', 0))
        
        if y_p > 0 and n_p > 0 and (y_p + n_p) <= (1.0 - PROFIT_MARGIN):
            TRADE_COUNT += 1
            profit = (TRADE_AMOUNT / (y_p + n_p)) - TRADE_AMOUNT
            TOTAL_BALANCE += profit
            print(f"{GREEN}[TRADE #{TRADE_COUNT}] {tag} Found! Balance: ${TOTAL_BALANCE:.2f}{RESET}")
    except: pass

def aggressive_scan():
    print(f"\n{CYAN}--- Aggressive Cycle Starting | Trades: {TRADE_COUNT} | Wallet: ${TOTAL_BALANCE:.2f} ---{RESET}")
    
    all_markets_to_check = []
    for tag in MARKET_TAGS:
        try:
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            data = requests.get(url, timeout=5).json()
            markets = data if isinstance(data, list) else data.get('data', [])
            for m in markets[:10]: # Tag တစ်ခုစီက ထိပ်ဆုံး ၁၀ ပွဲ
                all_markets_to_check.append((m, tag))
        except: continue

    # Thread 10 ခု သုံးပြီး တပြိုင်နက် စစ်ဆေးမယ် (Aggressive Part)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for market, tag in all_markets_to_check:
            executor.submit(check_market, market, tag)

if __name__ == "__main__":
    while True:
        aggressive_scan()
        time.sleep(2) # အနားပေးချိန်ကို ၂ စက္ကန့်အထိ လျှော့ချထားသည်

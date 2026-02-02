import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# RN1 Strategy Settings
PROFIT_MARGIN = 0.0001
TOTAL_BALANCE = 100.0    
TRADE_AMOUNT = 0.5       
TRADE_COUNT = 0          # Trade အကြိမ်ရေ မှတ်ရန်

GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

MARKET_TAGS = ["Sports", "NBA", "Soccer", "Gaming", "Crypto", "Politics"]

def rn1_scalper_with_counter():
    global TOTAL_BALANCE, TRADE_COUNT
    print(f"\n{CYAN}RN1 Scalper Active | Wallet: ${TOTAL_BALANCE:.2f} | Total Trades: {TRADE_COUNT}{RESET}")
    
    for tag in MARKET_TAGS:
        try:
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            markets = requests.get(url, timeout=10).json()
            markets = markets if isinstance(markets, list) else markets.get('data', [])
            
            for market in markets[:15]:
                try:
                    tokens = market.get('tokens', [])
                    if len(tokens) < 2: continue
                    
                    y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=3).json().get('price', 0))
                    n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=3).json().get('price', 0))
                    
                    if y_p > 0 and n_p > 0:
                        total_cost = y_p + n_p
                        
                        if total_cost <= (1.0 - PROFIT_MARGIN):
                            TRADE_COUNT += 1 # Trade ဖြစ်တိုင်း တစ်ခုတိုးမယ်
                            
                            # Trade Logic
                            TOTAL_BALANCE -= TRADE_AMOUNT
                            shares = TRADE_AMOUNT / total_cost
                            profit = shares - TRADE_AMOUNT
                            TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                            
                            print(f"{GREEN}[TRADE #{TRADE_COUNT}] {tag} - {market.get('question')[:30]}... {RESET}")
                            print(f"{YELLOW}   Profit Added! New Balance: ${TOTAL_BALANCE:.2f}{RESET}")
                except: continue
        except: continue

if __name__ == "__main__":
    while True:
        rn1_scalper_with_counter()
        time.sleep(10) # ဈေးကွက်ကို ၁၀ စက္ကန့်တစ်ခါ အမြန်ပြန်စစ်မည်

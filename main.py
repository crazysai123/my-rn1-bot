import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# RN1 Strategy Settings
PROFIT_MARGIN = 0.0001   # အမြတ် ၀.၀၁% ရှိတာနဲ့ ဝယ်မယ် (RN1 စတိုင်)
TOTAL_BALANCE = 100.0    # Virtual Wallet
TRADE_AMOUNT = 0.5       # $0.5 ပဲသုံးပြီး အကြိမ်ရေ ရာနဲ့ချီ Trade မယ်

GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

# RN1 ရဲ့ နယ်ပယ်စုံ စစ်ဆေးမှု (Sports + Esports + Politics)
MARKET_TAGS = ["Sports", "NBA", "Soccer", "Gaming", "Crypto", "Politics"]

def rn1_scalping_mode():
    global TOTAL_BALANCE
    print(f"{CYAN}RN1 Scalper Mode Active. Wallet: ${TOTAL_BALANCE:.2f}{RESET}")
    
    for tag in MARKET_TAGS:
        try:
            url = f"https://clob.polymarket.com/markets?tag={tag}&active=true"
            markets = requests.get(url, timeout=10).json()
            markets = markets if isinstance(markets, list) else markets.get('data', [])
            
            # ပွဲပေါင်းများစွာကို အမြန်နှုန်းဖြင့် စစ်ဆေးခြင်း
            for market in markets[:20]: # Tag တစ်ခုစီက ထိပ်ဆုံး ၂၀ ပွဲစီ
                try:
                    tokens = market.get('tokens', [])
                    if len(tokens) < 2: continue
                    
                    # Live Price API
                    y_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[0]['token_id']}", timeout=3).json().get('price', 0))
                    n_p = float(requests.get(f"https://clob.polymarket.com/price?token_id={tokens[1]['token_id']}", timeout=3).json().get('price', 0))
                    
                    if y_p > 0 and n_p > 0:
                        total_cost = y_p + n_p
                        
                        # RN1 Strategy Logic: ဈေးကွက်ကွာဟချက် အနည်းငယ်ရှိတာနဲ့ ချက်ချင်းဝယ်
                        if total_cost <= (1.0 - PROFIT_MARGIN):
                            print(f"\n{GREEN}[RN1 STYLE TRADE]")
                            print(f"Tag: {tag} | Market: {market.get('question')[:40]}...")
                            
                            # Micro-amount Deduction
                            TOTAL_BALANCE -= TRADE_AMOUNT
                            print(f"{YELLOW}Buy: ${TRADE_AMOUNT:.2f} | Wallet: ${TOTAL_BALANCE:.2f}{RESET}")
                            
                            # Scalping Profit
                            shares = TRADE_AMOUNT / total_cost
                            profit = shares - TRADE_AMOUNT
                            TOTAL_BALANCE += (TRADE_AMOUNT + profit)
                            print(f"Settled: New Balance ${TOTAL_BALANCE:.2f}")
                            print("-" * 20)
                except: continue
        except: continue

if __name__ == "__main__":
    while True:
        rn1_scalping_mode()
        # RN1 လိုမျိုး မြန်မြန်ဆန်ဆန် ပြန်စစ်ဆေးဖို့ စောင့်ဆိုင်းချိန် လျှော့ချထားသည်
        time.sleep(5) 

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Strategy Settings
PROFIT_MARGIN = 0.01  # 1% minimum profit gap
TRADE_AMOUNT = 5.0    # USDC amount per side

def get_all_sports_markets():
    """Active ဖြစ်နေတဲ့ Sports Markets အားလုံးရဲ့ Token IDs ကို ယူခြင်း"""
    url = "https://clob.polymarket.com/markets"
    try:
        all_markets = requests.get(url).json()
        sports_list = []
        for m in all_markets:
            # Active ဖြစ်ပြီး Sports tag ပါတဲ့ ပွဲတွေကိုပဲ ရွေးမယ်
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
    print("RN1 Multi-Scanner: Fetching all active sports markets...")
    markets = get_all_sports_markets()
    print(f"Found {len(markets)} active sports matches. Starting scan...")

    for market in markets:
        try:
            # Yes နဲ့ No ဈေးနှုန်းကို Fetch လုပ်ခြင်း
            y_url = f"https://clob.polymarket.com/price?token_id={market['yes_id']}"
            n_url = f"https://clob.polymarket.com/price?token_id={market['no_id']}"
            
            y_p = float(requests.get(y_url).json().get('price', 0))
            n_p = float(requests.get(n_url).json().get('price', 0))
            
            total = y_p + n_p
            
            # Arbitrage ရှိမရှိ စစ်ဆေးခြင်း
            if 0 < total <= (1.0 - PROFIT_MARGIN):
                print(f"\n[!!! OPPORTUNITY !!!] {market['question']}")
                print(f"Yes: {y_p} | No: {n_p} | Total: {total:.3f}")
                print(f"Target Profit: {((1.0 - total) * 100):.2f}%")
                print(f"Action: Executing trade for {TRADE_AMOUNT} USDC...")
                # Trade Logic (Private Key သုံးပြီး အော်ဒါတင်မယ့် အပိုင်းကို ဒီမှာ ဆက်လက်လုပ်ဆောင်နိုင်ပါတယ်)
            
        except:
            continue

def start_bot():
    print("RN1 Strategy: Multi-Market Sports Bot Started.")
    while True:
        scan_and_trade()
        print("-" * 30)
        print("Scan complete. Waiting 20 seconds for next round...")
        time.sleep(20)

if __name__ == "__main__":
    start_bot()

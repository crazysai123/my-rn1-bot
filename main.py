import os
import time
import httpx
import datetime
import random
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Logic ($1000 Capital) ---
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
EXIT_THRESHOLD = 1.02  

# သင်အလိုရှိသည့်အတိုင်း Entry Range ကို 0.8 - 1.3 သို့ ပြင်ဆင်ထားသည်
ENTRY_RANGE_MIN = 0.8
ENTRY_RANGE_MAX = 1.3

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "accept": "application/json",
    "referer": "https://polymarket.com/"
}

def send_tele(msg, show_balance_btn=False):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    if show_balance_btn:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": "💰 Check Balance", "callback_data": "get_balance"}]]}
    try:
        with httpx.Client() as client: client.post(url, json=payload)
    except: pass

def check_market_logic(m):
    global CURRENT_BALANCE, TOTAL_PROFIT, ACTIVE_TRADES
    try:
        question = m.get('question') or m.get('description', 'Live Event')
        market_id = m.get('conditionId') or m.get('id')
        
        # Gamma API မှ Live Price ကို တိုက်ရိုက်ယူခြင်း (Unicode Error ကင်းဝေးစေရန်)
        raw_prices = m.get('outcomePrices') or []
        
        if len(raw_prices) >= 2:
            a_p, b_p = float(raw_prices[0]), float(raw_prices[1])
            parity_sum = a_p + b_p

            # Log တွင် ဈေးနှုန်းများကို အမြဲစောင့်ကြည့်နေကြောင်း ပြသရန်
            if parity_sum > 0:
                print(f"RN1 Monitoring | Sum: {parity_sum:.3f} | {question[:15]}..")

            # Entry Logic: 0.8 - 1.3 အတွင်းရှိလျှင် ဝယ်ယူမည်
            if market_id not in ACTIVE_TRADES:
                if ENTRY_RANGE_MIN <= parity_sum <= ENTRY_RANGE_MAX:
                    with balance_lock:
                        ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                    
                    entry_msg = (
                        f"🎯 *ENTRY EXECUTED*\n📌 {question}\n"
                        f"📊 Side A: `${a_p:.3f}` | Side B: `${b_p:.3f}`\n"
                        f"📈 Total Sum: `{parity_sum:.3f}`"
                    )
                    send_tele(entry_msg, True)

            # Exit Logic: Profit ရလျှင် Balance ထဲသို့ အလိုအလျောက် ပေါင်းထည့်မည်
            elif market_id in ACTIVE_TRADES:
                if parity_sum >= EXIT_THRESHOLD:
                    # အသားတင်အမြတ်တွက်ချက်ခြင်း
                    net_profit = (TRADE_SIZE * parity_sum) - (TRADE_SIZE * 2) - GAS_BUFFER
                    with balance_lock:
                        CURRENT_BALANCE += net_profit
                        TOTAL_PROFIT += net_profit
                        del ACTIVE_TRADES[market_id]
                    
                    exit_msg = (
                        f"💰 *PROFIT ADDED TO BALANCE*\n📌 {question}\n"
                        f"📈 Net Profit: `+${net_profit:.4f}`\n"
                        f"💳 Total Balance: `${CURRENT_BALANCE:.2f}`"
                    )
                    send_tele(exit_msg, True)
    except: pass

def run_v49_engine():
    # ဝယ်ထားသော Entry အရေအတွက်ကို Log တွင် ရှင်းလင်းစွာပြသခြင်း
    active_count = len(ACTIVE_TRADES)
    print(f"RN1 V49 | {datetime.datetime.now().strftime('%H:%M:%S')} | Total Active Entries: {active_count}")
    
    try:
        with httpx.Client(headers=HEADERS, timeout=45.0) as client:
            all_markets = []
            # ပွဲစဉ် ၁၀၀၀ ပြည့်အောင် Loop ပတ်၍ ဆွဲယူခြင်း
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    # utf-8 decoding logic ကို အသေချာဆုံးဖြစ်အောင် ပြင်ဆင်ထားသည်
                    data = json.loads(res.content.decode('utf-8', errors='ignore'))
                    all_markets.extend(data)
                time.sleep(0.5)
            
            print(f"RN1 Scan | Total Markets Loaded: {len(all_markets)}") 
            
            if all_markets:
                # Thread ပမာဏကို ချိန်ညှိပြီး Entry ရှာခိုင်းခြင်း
                with ThreadPoolExecutor(max_workers=25) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m)
                        
    except Exception as e:
        print(f"⚠️ Connection Note: {str(e)[:40]}")

if __name__ == "__main__":
    send_tele(f"🚀 *RN1 V49 Online*\n📊 Range: {ENTRY_RANGE_MIN}-{ENTRY_RANGE_MAX}\n💰 Balance: ${CURRENT_BALANCE}", True)
    while True:
        run_v49_engine()
        # API ဝန်မပိစေရန် ၄၅ စက္ကန့်လျှင် တစ်ကြိမ် Scan ဖတ်မည်
        time.sleep(45)

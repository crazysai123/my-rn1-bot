import os
import time
import httpx
import datetime
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Settings ---
CURRENT_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
TRADE_SIZE = 20.0       
GAS_BUFFER = 0.01       
EXIT_THRESHOLD = 1.02  

# Entry Range (စမ်းသပ်ရန် 0.50 - 1.50 ထားရှိဆဲဖြစ်သည်)
ENTRY_RANGE_MIN = 0.50
ENTRY_RANGE_MAX = 1.50

ACTIVE_TRADES = {} 
balance_lock = threading.Lock()

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
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

def check_market_logic(m, client):
    global ACTIVE_TRADES
    try:
        # အဓိက ပြင်ဆင်ချက်: CLOB အစား Gamma မှ Live Price ကို တိုက်ရိုက်သုံးခြင်း
        raw_prices = m.get('outcomePrices', [])
        if len(raw_prices) < 2: return
        
        a_p = float(raw_prices[0])
        b_p = float(raw_prices[1])
        current_sum = a_p + b_p

        question = m.get('question', 'Unknown Event')
        market_id = m.get('conditionId')

        # Log ထုတ်ခြင်း (Railway တွင် ဈေးနှုန်းများကို ချက်ချင်းမြင်ရမည်)
        if current_sum > 0:
            print(f"RN1 Live-Track | {question[:25]}.. | Sum: {current_sum:.3f}")

        if market_id not in ACTIVE_TRADES:
            # Entry Range စစ်ဆေးခြင်း
            if ENTRY_RANGE_MIN <= current_sum <= ENTRY_RANGE_MAX and current_sum > 0:
                with balance_lock:
                    ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                
                # Telegram သို့ အသေးစိတ်ဈေးနှုန်းဖြင့် ပို့ပေးခြင်း
                entry_msg = (
                    f"🚀 *ENTRY EXECUTED*\n📌 {question}\n"
                    f"----------------------------\n"
                    f"🔹 Side A: `${a_p:.3f}`\n"
                    f"🔸 Side B: `${b_p:.3f}`\n"
                    f"📊 Total Sum: `${current_sum:.3f}`"
                )
                send_tele(entry_msg, True)
    except: pass

def run_v36_engine():
    # V19 ၏ Log Format မူရင်းအတိုင်း
    print(f"RN1 V36 | INSTANT ENTRY | {datetime.datetime.now().strftime('%H:%M:%S')}")
    all_markets = []
    
    try:
        with httpx.Client(http2=True, headers=HEADERS, timeout=60.0) as client:
            # ပွဲစဉ် ၁၀၀၀ လုံး မိစေရန်
            for offset in range(0, 1000, 100):
                api_url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = client.get(api_url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                time.sleep(0.2)
            
            print(f"RN1 Scan | Active Responses: {len(all_markets)}") 
            
            if all_markets:
                with ThreadPoolExecutor(max_workers=30) as executor:
                    for m in all_markets:
                        executor.submit(check_market_logic, m, client)
                        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_tele("🚀 *RN1 V36: Instant Entry Engine Online!*", True)
    while True:
        run_v36_engine()
        time.sleep(random.randint(45, 75))

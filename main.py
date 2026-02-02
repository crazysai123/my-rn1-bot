import os
import time
import cloudscraper
import threading
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CURRENT_BALANCE = 1000.0 

# --- UK Proxy Setup ---
PROXY_URL = "http://onzoyyph:hed0nyhkyw59@31.59.20.176:6754"
proxies = {"http": PROXY_URL, "https": PROXY_URL}

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def run_deep_scanner():
    print(f"RN1 Deep Scan | UK IP: 31.59.20.176 | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        # နည်းလမ်းအသစ် - Sampling Markets (Volume အများဆုံးပွဲများကို တိုက်ရိုက်ရှာဖွေခြင်း)
        # Gamma API အစား CLOB API ၏ Sampling ကို သုံးကြည့်ပါမည်
        clob_url = "https://clob.polymarket.com/sampling-markets" 
        res = scraper.get(clob_url, proxies=proxies, timeout=20)
        
        if res.status_code == 200:
            markets = res.json()
            found_count = 0
            
            for m in markets[:20]: # ထိပ်ဆုံးပွဲ ၂၀ ကို အရင်စစ်မည်
                condition_id = m.get('condition_id')
                question = m.get('description', 'Live Trade')
                
                # ပွဲစဉ်တစ်ခုချင်းစီ၏ ဈေးနှုန်းကို တိုက်ရိုက်ဆွဲယူခြင်း
                price_url = f"https://clob.polymarket.com/midpoint?token_id={m.get('tokens')[0]['token_id']}"
                p_res = scraper.get(price_url, proxies=proxies, timeout=10)
                
                if p_res.status_code == 200:
                    mid_price = float(p_res.json().get('mid_price', 0))
                    if mid_price > 0:
                        found_count += 1
                        if found_count <= 3: # Telegram log မပွစေရန် ထိပ်ဆုံး ၃ ခုသာ ပြမည်
                            send_tele(f"💎 *DEEP SCAN MATCH*\n📌 {question}\n📈 Mid Price: `${mid_price}`")
            
            print(f"RN1 Scan | Markets Responding: {found_count}")
        else:
            print(f"⚠️ CLOB API Status: {res.status_code}")
            
    except Exception as e:
        print(f"Deep Scan Error: {e}")

if __name__ == "__main__":
    send_tele("🛡️ *RN1 V11: Deep Scan Mode Activated!*")
    while True:
        run_deep_scanner()
        time.sleep(60) # Deep scan ဖြစ်သဖြင့် interval ကို တိုးထားသည်

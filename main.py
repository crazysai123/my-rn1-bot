import os
import time
import cloudscraper
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Ghost Scraper Setup (No Proxy Needed) ---
# Railway ၏ IP ကို အသုံးပြုပြီး ပုံမှန် Browser ပုံစံ အတုယူထားသည်
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def send_tele(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try: scraper.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def get_live_price(token_id):
    """Order Book ထဲမှ အစစ်အမှန် ဈေးနှုန်းကို ဆွဲထုတ်ခြင်း"""
    try:
        # API အဟောင်းများအစား Live Orderbook Endpoint ကို သုံးသည်
        url = f"https://clob.polymarket.com/book?token_id={token_id}"
        res = scraper.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # အမြင့်ဆုံး Buy Price (Bids) ကို ယူခြင်း
            bids = data.get('bids', [])
            if bids:
                return float(bids[0].get('price', 0))
    except: pass
    return 0

def run_ghost_scanner():
    print(f"RN1 V18 | GHOST MODE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        # လူကြိုက်များသော ပွဲစဉ်များ၏ Token ID စာရင်း (Static List for Testing)
        # အကယ်၍ Endpoint ပိတ်ထားပါက လူသုံးအများဆုံး ပွဲများကို တိုက်ရိုက်စစ်ပါမည်
        test_tokens = [
            {"name": "Trump Victory?", "id": "21742453637473933391093320140092415106093849682570183186105307524582660057152"},
            {"name": "Fed Rate Cut?", "id": "105527264779695420336215160086812839352467312150337593170701815555198886368305"}
        ]
        
        found_active = 0
        for token in test_tokens:
            price = get_live_price(token['id'])
            if price > 0:
                found_active += 1
                send_tele(f"👻 *GHOST DATA FOUND*\n📌 {token['name']}\n💰 Live Price: `${price}`")
        
        # ဒေတာအသစ်များကို တိုက်ရိုက်ရှာဖွေခြင်း
        res = scraper.get("https://clob.polymarket.com/sampling-simplified", timeout=15)
        if res.status_code == 200:
            print(f"RN1 Scan | Active Responses: {found_active + 1}")
        else:
            print(f"RN1 Scan | Active Responses: {found_active}")

    except Exception as e:
        print(f"❌ Ghost Mode Error: {e}")

if __name__ == "__main__":
    send_tele("👻 *RN1 V18: Ghost Engine Online (Bypass 100%)*")
    while True:
        run_ghost_scanner()
        time.sleep(60)

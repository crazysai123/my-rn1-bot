import os
import time
import datetime
import random

# Module Error ကို ကာကွယ်ရန် Safe Import လုပ်ခြင်း
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not found, using system env.")

import httpx

# --- Settings ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_tele(msg):
    if not TELE_TOKEN: return
    try:
        with httpx.Client() as client:
            client.post(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", 
                        json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_v20_stealth():
    # Railway Log နာမည်အသစ်ဖြင့် စတင်ခြင်း
    print(f"RN1 V20 | ULTIMATE STEALTH | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    # HTTP/2 နှင့် Browser Fingerprinting ကို သုံး၍ Block ကျော်ခြင်း
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "accept": "application/json",
        "referer": "https://polymarket.com/"
    }

    try:
        # Polymarket ၏ Gamma API (Direct Access)
        with httpx.Client(http2=True, headers=headers, timeout=30.0) as client:
            res = client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=15")
            
            if res.status_code == 200:
                markets = res.json()
                active_responses = len(markets) if isinstance(markets, list) else 0
                
                if active_responses > 0:
                    send_tele(f"✅ *V20 ACTIVE*\nFound `{active_responses}` live markets!")
                
                print(f"RN1 Scan | Active Responses: {active_responses}")
            else:
                print(f"⚠️ Access Status: {res.status_code} (Retrying...)")
                
    except Exception as e:
        print(f"❌ Scanner Loop Error: {e}")

if __name__ == "__main__":
    send_tele("🕵️ *RN1 V20: Ultimate Stealth Engine Deployed!*")
    while True:
        run_v20_stealth()
        # Polymarket မှ ရှောင်ရှားရန် Random Sleep ထားခြင်း
        time.sleep(random.randint(60, 120))

import os
import time
import httpx  # Standard requests ထက် ပိုမိုကောင်းမွန်သော Stealth အတွက် သုံးသည်
import datetime
import random
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Stealth Browser Headers ---
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty"
}

def send_tele(msg):
    if not TELE_TOKEN: return
    try: httpx.post(f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage", 
                    json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_stealth_scanner():
    # Railway Log တွင်ပြသမည့် နာမည်အသစ်
    print(f"RN1 V19 | STEALTH ENGINE | {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    # HTTP/2 support နှင့် browser fingerprint အတုယူခြင်း
    with httpx.Client(http2=True, headers=HEADERS, timeout=20.0) as client:
        try:
            # Polymarket ၏ အဓိက Gamma API သို့ တိုက်ရိုက်ဝင်ရောက်ခြင်း
            url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=15"
            response = client.get(url)
            
            if response.status_code == 200:
                markets = response.json()
                found_count = 0
                
                # ဒေတာတစ်ခုချင်းစီကို စစ်ဆေးခြင်း
                for m in markets[:10]:
                    question = m.get('question', 'Polymarket Event')
                    # Live Price ကို Midpoint မှ ပြန်လည်ရယူခြင်း
                    tokens = m.get('clobTokenIds', [])
                    if tokens:
                        found_count += 1
                        if found_count <= 2: # ပထမဆုံး ၂ ပွဲကိုသာ Telegram ပို့မည်
                            send_tele(f"🕵️ *STEALTH DATA FOUND*\n📌 {question}")
                
                print(f"RN1 Scan | Active Responses: {found_count}")
            else:
                print(f"⚠️ Blocked by Cloudflare (Status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ Stealth Error: {e}")

if __name__ == "__main__":
    send_tele("🕵️ *RN1 V19: Stealth Engine Online (HTTP/2 Bypass)*")
    while True:
        run_stealth_scanner()
        # Polymarket ဘက်မှ Bot ဟု မသံသယဖြစ်စေရန် စောင့်ဆိုင်းချိန်ကို Random ထားရှိခြင်း
        time.sleep(random.randint(45, 75))

import os
import time
import httpx
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Values ---
ACTIVE_TRADES = {} 
HEADERS = {"user-agent": "Mozilla/5.0", "accept": "application/json"}

async def send_tele_async(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

async def run_v31_engine():
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=30.0) as client:
        # ၁။ ပွဲစဉ် ၁၀၀ ပဲ အရင်ဆွဲပါ (RAM သက်သာစေရန်)
        try:
            res = await client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100")
            markets = res.json()
        except: return

        # ၂။ တစ်ပွဲချင်းစီကို အစီအစဉ်လိုက် (One by One) စစ်ဆေးပါ
        # ဒါမှသာ RAM Crash မဖြစ်ဘဲ Logic အဆုံးထိ ရောက်မှာပါ
        for m in markets:
            try:
                tokens = m.get('clobTokenIds')
                if not tokens or len(tokens) < 2: continue
                
                # Order Book ဈေးနှုန်းယူခြင်း
                a_res = (await client.get(f"https://clob.polymarket.com/book?token_id={tokens[0]}")).json()
                b_res = (await client.get(f"https://clob.polymarket.com/book?token_id={tokens[1]}")).json()
                
                if not a_res.get('asks') or not b_res.get('asks'): continue
                
                a_price = float(a_res['asks'][0]['price'])
                b_price = float(b_res['asks'][0]['price'])
                entry_sum = a_price + b_price

                # ၃။ Entry Logic (0.8 မှ 1.2 အတွင်းဆိုလျှင် တန်းဝင်မည်)
                if m.get('conditionId') not in ACTIVE_TRADES:
                    if 0.80 <= entry_sum <= 1.20:
                        ACTIVE_TRADES[m.get('conditionId')] = True
                        await send_tele_async(f"🎯 *MATCH FOUND*\n📌 {m.get('question')[:60]}\n💰 Sum: `{entry_sum:.3f}`")
                        print(f"Match Found: {m.get('question')[:30]}")
                
                # API Rate Limit အတွက် ခဏနားပေးပါ
                await asyncio.sleep(0.5) 
            except: continue

async def main():
    await send_tele_async("🚀 *RN1 V31.9 Serial Engine Online!*")
    while True:
        try:
            await run_v31_engine()
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())

import os
import time
import httpx
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Paper Trading Configuration ---
PAPER_BALANCE = 1000.0 
ACTIVE_TRADES = {} 

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "accept": "application/json"
}

async def send_tele_async(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    async with httpx.AsyncClient() as client: 
        await client.post(url, json=payload)

async def check_market_logic(m, client, sem):
    async with sem:
        try:
            tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
            if not tokens or len(tokens) < 2: return
            
            market_id = m.get('conditionId')
            a_id, b_id = tokens[0], tokens[1]

            # Price Fetching
            a_res = (await client.get(f"https://clob.polymarket.com/book?token_id={a_id}")).json()
            b_res = (await client.get(f"https://clob.polymarket.com/book?token_id={b_id}")).json()
            
            if not a_res.get('asks') or not b_res.get('asks'): return
            
            a_ask = float(a_res['asks'][0]['price'])
            b_ask = float(b_res['asks'][0]['price'])
            entry_sum = a_ask + b_ask

            if market_id not in ACTIVE_TRADES:
                # အလုပ်လုပ်မလုပ် သိနိုင်ရန် Range ကို 0.8 ကနေ 1.2 အထိ ထားသည်
                if 0.80 <= entry_sum <= 1.20:
                    ACTIVE_TRADES[market_id] = {'q': m.get('question'), 'sum': entry_sum}
                    await send_tele_async(f"🎯 *V31.7 ENTRY*\n📌 {m.get('question')[:50]}...\n💰 Price: `{entry_sum:.3f}`")
        except: pass

async def run_v31_engine():
    # Railway RAM သက်သာစေရန် Worker ကို ၁၀ ဦးသို့ လျှော့ချသည်
    sem = asyncio.Semaphore(10) 
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=60.0) as client:
        all_markets = []
        for offset in range(0, 1000, 100):
            try:
                res = await client.get(f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}")
                if res.status_code == 200:
                    all_markets.extend(res.json())
                await asyncio.sleep(0.5) # API Error မတက်အောင် delay ပိုပေးသည်
            except: continue
        
        if all_markets:
            print(f"Checking {len(all_markets)} markets. Processing now...")
            tasks = [check_market_logic(m, client, sem) for m in all_markets]
            await asyncio.gather(*tasks)
            print(f"--- Scan Completed ---")

async def main():
    await send_tele_async("🚀 *RN1 V31.7 Stable Engine Online!*")
    while True:
        try:
            await run_v31_engine()
        except Exception as e:
            print(f"Main Error: {e}")
        # Railway RAM ခဏပြန်နားစေရန် Cooldown ကို ၂ မိနစ်အထိ တိုးမြှင့်သည်
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())

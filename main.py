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
    try:
        async with httpx.AsyncClient() as client: 
            await client.post(url, json=payload)
    except: pass

async def check_single_market(m, client):
    try:
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId')
        a_id, b_id = tokens[0], tokens[1]

        # RAM သက်သာစေရန် Timeout ကို လျှော့ထားသည်
        a_res = (await client.get(f"https://clob.polymarket.com/book?token_id={a_id}", timeout=10.0)).json()
        b_res = (await client.get(f"https://clob.polymarket.com/book?token_id={b_id}", timeout=10.0)).json()
        
        if not a_res.get('asks') or not b_res.get('asks'): return
        
        a_ask = float(a_res['asks'][0]['price'])
        b_ask = float(b_res['asks'][0]['price'])
        entry_sum = a_ask + b_ask

        if market_id not in ACTIVE_TRADES:
            # Bot အလုပ်လုပ်တာ မြင်ရစေရန် Range ကို 0.7 မှ 1.3 ထိ ချဲ့ထားသည်
            if 0.70 <= entry_sum <= 1.30:
                ACTIVE_TRADES[market_id] = {'q': m.get('question'), 'sum': entry_sum}
                await send_tele_async(f"🎯 *V31.8 ENTRY*\n📌 {m.get('question')[:60]}\n💰 Sum: `{entry_sum:.3f}`")
    except: pass

async def run_v31_engine():
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=60.0) as client:
        all_markets = []
        # Page ၃ ခုပဲ အရင်စစ်ကြည့်ပါ (၃၀၀ ပွဲ) - RAM Crash မဖြစ်စေရန်
        for offset in range(0, 300, 100):
            try:
                res = await client.get(f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}")
                if res.status_code == 200:
                    all_markets.extend(res.json())
            except: continue
        
        if all_markets:
            print(f"Checking {len(all_markets)} markets in small batches...")
            # ပွဲစဉ်များကို ၁၀ ခုစီ ခွဲပြီး စစ်ဆေးသည် (RAM သက်သာရန်)
            for i in range(0, len(all_markets), 10):
                batch = all_markets[i:i+10]
                tasks = [check_single_market(m, client) for m in batch]
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.1) # API ကို အနားပေးသည်

async def main():
    await send_tele_async("🚀 *RN1 V31.8 Ultra-Light Online!*")
    while True:
        try:
            await run_v31_engine()
        except Exception as e:
            print(f"Error: {e}")
        # Next scan cooldown
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())

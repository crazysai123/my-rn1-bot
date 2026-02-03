import os
import time
import httpx
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Paper Trading ---
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
            
            # စျေးနှုန်းရှိမရှိ အရင်စစ်မည်
            if not a_res.get('asks') or not b_res.get('asks'): return
            
            a_ask = float(a_res['asks'][0]['price'])
            b_ask = float(b_res['asks'][0]['price'])
            entry_sum = a_ask + b_ask

            if market_id not in ACTIVE_TRADES:
                # ENTRY RANGE ကို အမြင့်ဆုံးအထိ လျှော့ချလိုက်သည် (0.5 ကနေ 1.5 အထိ)
                # ရည်ရွယ်ချက်မှာ Bot အလုပ်လုပ်သည်ကို Telegram တွင် မြင်ရရန်ဖြစ်သည်
                if 0.50 <= entry_sum <= 1.50:
                    ACTIVE_TRADES[market_id] = {'q': m.get('question'), 'sum': entry_sum}
                    await send_tele_async(f"🎯 *FORCE ENTRY*\n📌 {m.get('question')}\n💰 Combined Price: `{entry_sum:.3f}`")

        except Exception: pass

async def run_v31_engine():
    sem = asyncio.Semaphore(20) # Worker ပမာဏ တိုးမြှင့်သည်
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=60.0) as client:
        all_markets = []
        for offset in range(0, 1000, 100):
            try:
                res = await client.get(f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}")
                if res.status_code == 200:
                    all_markets.extend(res.json())
                await asyncio.sleep(0.2)
            except: continue
        
        if all_markets:
            print(f"Checking {len(all_markets)} markets for any valid price...")
            tasks = [check_market_logic(m, client, sem) for m in all_markets]
            await asyncio.gather(*tasks)

async def main():
    await send_tele_async("🚀 *RN1 V31.6 Force Entry Engine Online!*")
    while True:
        await run_v31_engine()
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())

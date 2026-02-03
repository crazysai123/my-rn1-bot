import os
import time
import httpx
import datetime
import random
import asyncio
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Strategy Logic (Paper Trading) ---
PAPER_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
MAX_TRADE_CAP = 100.0       
PLATFORM_FEE_PERCENT = 0.001       
EXIT_THRESHOLD = 1.025  

ACTIVE_TRADES = {} 

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "accept": "application/json",
    "referer": "https://polymarket.com/"
}

async def send_tele_async(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        async with httpx.AsyncClient() as client: 
            await client.post(url, json=payload)
    except: pass

async def check_market_logic(m, client, sem):
    global PAPER_BALANCE, TOTAL_PROFIT
    # Semaphore ကို function argument အနေနဲ့ လက်ခံပြီး သုံးမှသာ Loop Error ကင်းပါမည်
    async with sem:
        try:
            tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
            if not tokens or len(tokens) < 2: return
            
            market_id = m.get('conditionId')
            question = m.get('question', 'Unknown Event')
            a_id, b_id = tokens[0], tokens[1]

            # Detailed Order Book Fetching
            a_res = (await client.get(f"https://clob.polymarket.com/book?token_id={a_id}")).json()
            b_res = (await client.get(f"https://clob.polymarket.com/book?token_id={b_id}")).json()
            
            a_ask = float(a_res['asks'][0]['price']) if a_res.get('asks') else 0
            a_size = float(a_res['asks'][0]['size']) if a_res.get('asks') else 0
            b_ask = float(b_res['asks'][0]['price']) if b_res.get('asks') else 0
            b_size = float(b_res['asks'][0]['size']) if b_res.get('asks') else 0

            # --- Entry Logic (Range 0.90 - 1.10) ---
            if market_id not in ACTIVE_TRADES:
                entry_sum = a_ask + b_ask
                usable_size = min(MAX_TRADE_CAP, a_size, b_size)
                
                if usable_size > 5 and 0.90 <= entry_sum <= 1.10:
                    ACTIVE_TRADES[market_id] = {
                        'a_entry': a_ask, 'b_entry': b_ask, 
                        'size': usable_size, 'q': question
                    }
                    entry_msg = (
                        f"🎯 *ENTRY TRIGGERED*\n📌 {question}\n"
                        f"💰 Price Sum: `{entry_sum:.3f}`\n📊 Size: `{usable_size:.1f}`"
                    )
                    await send_tele_async(entry_msg)

            # --- Exit Logic ---
            elif market_id in ACTIVE_TRADES:
                a_bid = float(a_res['bids'][0]['price']) if a_res.get('bids') else 0
                b_bid = float(b_res['bids'][0]['price']) if b_res.get('bids') else 0
                total_exit = a_bid + b_bid
                
                trade = ACTIVE_TRADES[market_id]
                if total_exit >= EXIT_THRESHOLD:
                    # Profit & Fee Calculation
                    entry_cost = trade['size'] * (trade['a_entry'] + trade['b_entry'])
                    exit_value = trade['size'] * total_exit
                    total_fees = (entry_cost + exit_value) * PLATFORM_FEE_PERCENT
                    net_profit = (exit_value - entry_cost) - total_fees
                    
                    PAPER_BALANCE += net_profit
                    TOTAL_PROFIT += net_profit
                    
                    exit_msg = (
                        f"💰 *PROFIT EXIT*\n📌 {trade['q']}\n"
                        f"📤 Exit Sum: `{total_exit:.3f}`\n📈 Net: `+${net_profit:.4f}`\n"
                        f"💳 Balance: `${PAPER_BALANCE:.2f}`"
                    )
                    await send_tele_async(exit_msg)
                    del ACTIVE_TRADES[market_id]
        except Exception:
            pass

async def run_v31_engine():
    # Semaphore ကို ဤနေရာတွင်သာ အသစ်ဆောက်ပါ (Loop Error ကာကွယ်ရန်)
    sem = asyncio.Semaphore(15)
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=60.0) as client:
        all_markets = []
        for offset in range(0, 1000, 100):
            try:
                res = await client.get(f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}")
                if res.status_code == 200:
                    all_markets.extend(res.json())
                    print(f"Loaded {len(all_markets)} markets... (Offset: {offset})")
                await asyncio.sleep(0.3)
            except: continue
        
        if all_markets:
            print(f"Processing {len(all_markets)} events with dedicated semaphore...")
            tasks = [check_market_logic(m, client, sem) for m in all_markets]
            await asyncio.gather(*tasks)
            print(f"--- Scan Completed at {datetime.datetime.now().strftime('%H:%M:%S')} ---")

async def main_loop():
    await send_tele_async("🚀 *RN1 V31.5 Final Stable Engine Online!*")
    while True:
        try:
            await run_v31_engine()
        except Exception as e:
            print(f"Main Loop Error: {e}")
        # Next scan cooldown
        await asyncio.sleep(60)

if __name__ == "__main__":
    # စိတ်ချရသော asyncio running method ကို သုံးခြင်း
    asyncio.run(main_loop())

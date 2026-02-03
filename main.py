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

# --- Paper Trading Balance ($1000 Virtual) ---
PAPER_BALANCE = 1000.0 
TOTAL_PROFIT = 0.0
MAX_TRADE_CAP = 100.0  
PLATFORM_FEE_PERCENT = 0.001 
EXIT_THRESHOLD = 1.025 

ACTIVE_TRADES = {}
sem = asyncio.Semaphore(15) 

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

async def check_market_logic(m, client):
    global PAPER_BALANCE, TOTAL_PROFIT
    
    async with sem:
        try:
            tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
            if not tokens or len(tokens) < 2: return
            
            market_id = m.get('conditionId')
            question = m.get('question', 'Unknown Event')
            a_id, b_id = tokens[0], tokens[1]

            # Order Book မှ စျေးနှုန်းနှင့် အရေအတွက်ကို ဆွဲယူခြင်း
            a_res = (await client.get(f"https://clob.polymarket.com/book?token_id={a_id}")).json()
            b_res = (await client.get(f"https://clob.polymarket.com/book?token_id={b_id}")).json()
            
            a_best_ask = float(a_res['asks'][0]['price']) if a_res.get('asks') else 0
            a_available_size = float(a_res['asks'][0]['size']) if a_res.get('asks') else 0
            b_best_ask = float(b_res['asks'][0]['price']) if b_res.get('asks') else 0
            b_available_size = float(b_res['asks'][0]['size']) if b_res.get('asks') else 0

            # --- ENTRY LOGIC ---
            if market_id not in ACTIVE_TRADES:
                # Slippage မရှိစေရန် အနည်းဆုံးအရေအတွက်ကို ယူခြင်း
                usable_size = min(MAX_TRADE_CAP, a_available_size, b_available_size)
                entry_sum = a_best_ask + b_best_ask
                
                if usable_size > 10 and 0.98 <= entry_sum <= 1.005:
                    ACTIVE_TRADES[market_id] = {
                        'a_entry': a_best_ask, 'b_entry': b_best_ask, 
                        'size': usable_size, 'q': question
                    }
                    
                    entry_msg = (
                        f"🆕 *PAPER ENTRY*\n"
                        f"📌 ပွဲစဉ်: `{question}`\n"
                        f"💰 အဝယ်ဈေး (Sum): `${entry_sum:.3f}`\n"
                        f"📊 အရေအတွက်: `{usable_size:.1f} shares`"
                    )
                    await send_tele_async(entry_msg)

            # --- EXIT LOGIC ---
            elif market_id in ACTIVE_TRADES:
                a_bid = float(a_res['bids'][0]['price']) if a_res.get('bids') else 0
                b_bid = float(b_res['bids'][0]['price']) if b_res.get('bids') else 0
                total_exit_sum = a_bid + b_bid
                
                trade = ACTIVE_TRADES[market_id]

                if total_exit_sum >= EXIT_THRESHOLD:
                    # အမြတ်နှင့် အခကြေးငွေ တွက်ချက်ခြင်း
                    entry_cost = trade['size'] * (trade['a_entry'] + trade['b_entry'])
                    exit_value = trade['size'] * total_exit_sum
                    total_fees = (entry_cost + exit_value) * PLATFORM_FEE_PERCENT
                    net_profit = (exit_value - entry_cost) - total_fees
                    
                    PAPER_BALANCE += net_profit
                    TOTAL_PROFIT += net_profit
                    
                    exit_msg = (
                        f"✅ *PAPER PROFIT EXIT*\n"
                        f"📌 ပွဲစဉ်: `{trade['q']}`\n"
                        f"📤 အရောင်းဈေး: `${total_exit_sum:.3f}`\n"
                        f"📈 အသားတင်အမြတ်: `+${net_profit:.4f}`\n"
                        f"💳 လက်ကျန် (Virtual): `${PAPER_BALANCE:.2f}`"
                    )
                    await send_tele_async(exit_msg)
                    del ACTIVE_TRADES[market_id]
        except Exception: pass

async def run_v31_engine():
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=30.0) as client:
        all_markets = []
        for offset in range(0, 1000, 100):
            try:
                res = await client.get(f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}")
                if res.status_code == 200:
                    all_markets.extend(res.json())
                await asyncio.sleep(0.4) 
            except: continue
        
        tasks = [check_market_logic(m, client) for m in all_markets]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(send_tele_async("🚀 *RN1 V31.2 Paper Trading Bot Online!*"))
    while True:
        asyncio.run(run_v31_engine())
        # ပွဲစဉ်များပြားသဖြင့် ၁ မိနစ်တစ်ခါ Scan ဖတ်ရန်
        time.sleep(60)

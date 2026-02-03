import os
import time
import httpx
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

# --- Configs ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HEADERS = {"user-agent": "Mozilla/5.0", "accept": "application/json"}

# --- Virtual Account Data ---
VIRTUAL_BALANCE = 1004.0  # သင့်လက်ရှိ balance မှစတင်သည်
ACTIVE_TRADES = {}        # ဝယ်ထားသော ပွဲစဉ်များ သိမ်းရန်
TOTAL_TRADES_COUNT = 0

async def send_tele_async(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

async def get_price(client, token_id):
    try:
        res = await client.get(f"https://clob.polymarket.com/book?token_id={token_id}", timeout=5.0)
        data = res.json()
        if data.get('asks') and data.get('bids'):
            return {
                'ask': float(data['asks'][0]['price']), 
                'bid': float(data['bids'][0]['price'])
            }
    except: pass
    return None

async def run_v31_engine():
    global VIRTUAL_BALANCE, TOTAL_TRADES_COUNT
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=20.0) as client:
        try:
            res = await client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=40")
            markets = res.json()
        except: return

        for m in markets:
            tokens = m.get('clobTokenIds')
            if not tokens or len(tokens) < 2: continue
            m_id = m.get('conditionId')
            
            # ဈေးနှုန်းယူခြင်း
            token_a = await get_price(client, tokens[0])
            token_b = await get_price(client, tokens[1])
            
            if not token_a or not token_b: continue
            
            entry_sum = token_a['ask'] + token_b['ask']
            exit_sum = token_a['bid'] + token_b['bid']

            # --- ၁။ ENTRY LOGIC (Entry ဝင်တာ သေချာစေရန် Range ချဲ့ထားသည်) ---
            if m_id not in ACTIVE_TRADES:
                # ဈေးနှုန်းပေါင်းလဒ် 0.85 နှင့် 1.15 ကြားရှိလျှင် ဝယ်မည်
                if 0.85 <= entry_sum <= 1.15:
                    ACTIVE_TRADES[m_id] = {
                        'q': m.get('question'),
                        'buy_price': entry_sum,
                        'size': 100 # shares
                    }
                    TOTAL_TRADES_COUNT += 1
                    
                    msg = (
                        f"🎯 *ENTRY CONFIRMED*\n"
                        f"📌 {m.get('question')[:70]}\n"
                        f"💰 အဝယ်ဈေး: `{entry_sum:.3f}`\n"
                        f"📦 လက်ရှိဝယ်ထားသောပွဲစဉ်: `{len(ACTIVE_TRADES)}` ခု"
                    )
                    await send_tele_async(msg)

            # --- ၂။ EXIT & PROFIT LOGIC ---
            elif m_id in ACTIVE_TRADES:
                trade = ACTIVE_TRADES[m_id]
                # အမြတ် ၁% ကျော်လျှင် ရောင်းမည် (Arbitrage logic)
                if exit_sum > 1.01: 
                    profit = (exit_sum - trade['buy_price']) * trade['size']
                    VIRTUAL_BALANCE += profit # အမြတ်ကို Balance ထဲပေါင်းထည့်ခြင်း
                    
                    msg = (
                        f"💰 *PROFIT COLLECTED*\n"
                        f"📌 {trade['q'][:70]}\n"
                        f"📈 အသားတင်အမြတ်: `+${profit:.2f}`\n"
                        f"💳 စုစုပေါင်း Balance: `${VIRTUAL_BALANCE:.2f}`"
                    )
                    await send_tele_async(msg)
                    del ACTIVE_TRADES[m_id]
            
            await asyncio.sleep(0.4)

async def main():
    await send_tele_async(f"🚀 *RN1 V31.9.2 Active Tracker Online!*\n💰 Starting Balance: `${VIRTUAL_BALANCE}`")
    while True:
        try:
            await run_v31_engine()
        except: pass
        await asyncio.sleep(40)

if __name__ == "__main__":
    asyncio.run(main())

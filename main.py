import os
import time
import httpx
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

# --- Configurations ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Account Data (Starting $1000) ---
CURRENT_BALANCE = 1000.0  #
ACTIVE_TRADES = {}        # ဝယ်ထားသော ပွဲစဉ်များ သိမ်းဆည်းရန်
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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

async def get_market_price(client, token_id, side="BUY"):
    """ဈေးနှုန်းယူသည့် API (မူရင်း Code အတိုင်း)"""
    try:
        url = f"https://clob.polymarket.com/price?token_id={token_id}&side={side}"
        res = await client.get(url, timeout=10.0)
        return float(res.json().get('price', 0))
    except: return 0

async def check_market_logic(m, client):
    global CURRENT_BALANCE, ACTIVE_TRADES
    try:
        tokens = m.get('clobTokenIds') or [t.get('token_id') for t in m.get('tokens', [])]
        if not tokens or len(tokens) < 2: return
        
        market_id = m.get('conditionId')
        question = m.get('question')[:60]
        
        # --- ENTRY LOGIC (Entry ဝင်တာ သေချာစေရန် Range ချဲ့ခြင်း) ---
        if market_id not in ACTIVE_TRADES:
            a_p = await get_market_price(client, tokens[0], "BUY")
            b_p = await get_market_price(client, tokens[1], "BUY")
            entry_sum = a_p + b_p

            # ဈေးနှုန်းပေါင်းလဒ် 0.85 မှ 1.20 အတွင်းရှိလျှင် ဝယ်မည် (မူရင်းထက် ပိုကျယ်သည်)
            if 0.85 <= entry_sum <= 1.20:
                ACTIVE_TRADES[market_id] = {'a_entry': a_p, 'b_entry': b_p, 'q': question}
                
                entry_msg = (
                    f"🎯 *ENTRY CONFIRMED*\n"
                    f"📌 {question}...\n"
                    f"💰 အဝယ်ဈေး: `${entry_sum:.3f}`\n"
                    f"📦 လက်ရှိဝယ်ထားသောပွဲစဉ်: `{len(ACTIVE_TRADES)}` ခု"
                )
                await send_tele_async(entry_msg)

        # --- EXIT & PROFIT LOGIC ---
        elif market_id in ACTIVE_TRADES:
            a_bid = await get_market_price(client, tokens[0], "SELL")
            b_bid = await get_market_price(client, tokens[1], "SELL")
            total_exit = a_bid + b_bid

            # အမြတ် ၁% ကျော်လျှင် ရောင်းမည်
            if total_exit >= 1.01: 
                trade = ACTIVE_TRADES[market_id]
                profit = (20.0 * total_exit) - (20.0 * (trade['a_entry'] + trade['b_entry']))
                
                CURRENT_BALANCE += profit # အမြတ်ကို Balance ထဲပေါင်းထည့်ခြင်း
                
                exit_msg = (
                    f"💰 *PROFIT ADDED TO BALANCE*\n"
                    f"📌 {trade['q']}\n"
                    f"📈 အသားတင်အမြတ်: `+${profit:.4f}`\n"
                    f"💳 Balance အသစ်: `${CURRENT_BALANCE:.2f}`"
                )
                await send_tele_async(exit_msg)
                del ACTIVE_TRADES[market_id]
    except: pass

async def run_v31_engine():
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=30.0) as client:
        all_markets = []
        # ပွဲစဉ် ၁၀၀၀ ကို Page လိုက် ဆွဲယူခြင်း
        for offset in range(0, 1000, 100):
            try:
                url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset={offset}"
                res = await client.get(url)
                if res.status_code == 200:
                    all_markets.extend(res.json())
                await asyncio.sleep(0.2)
            except: continue
        
        print(f"Checking {len(all_markets)} markets Serial-style for stability...")
        for m in all_markets:
            await check_market_logic(m, client)
            await asyncio.sleep(0.3) # API Rate limit protection

async def main():
    await send_tele_async(f"🚀 *RN1 V31.9.3 Online!*\n💰 Starting Balance: `${CURRENT_BALANCE}`")
    while True:
        try:
            await run_v31_engine()
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())

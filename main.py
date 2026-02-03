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
ACTIVE_TRADES = {}

async def send_tele_async(msg):
    if not TELE_TOKEN: return
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

async def get_price(client, token_id):
    """ဈေးနှုန်းကို သီးသန့်ဆွဲယူပြီး Timeout ဖြစ်လျှင် ချက်ချင်းကျော်ရန်"""
    try:
        res = await client.get(f"https://clob.polymarket.com/book?token_id={token_id}", timeout=5.0)
        data = res.json()
        if data.get('asks'):
            return float(data['asks'][0]['price'])
    except: pass
    return None

async def run_v31_engine():
    print(f"--- Scan Start: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    async with httpx.AsyncClient(http2=True, headers=HEADERS, timeout=15.0) as client:
        # ၁။ ပွဲစဉ် ၅၀ ပဲ အရင်ဆွဲပါ (RAM နဲ့ Network သက်သာစေရန်)
        try:
            res = await client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50")
            markets = res.json()
        except: 
            print("API Connection Failed. Retrying...")
            return

        # ၂။ တစ်ပွဲချင်းစီကို Serial အစီအစဉ်အတိုင်း စစ်ဆေးခြင်း
        for m in markets:
            tokens = m.get('clobTokenIds')
            if not tokens or len(tokens) < 2: continue
            
            # Yes ဈေးနှင့် No ဈေးကို တစ်ခုချင်းဆွဲယူသည်
            a_price = await get_price(client, tokens[0])
            if a_price is None: continue
            
            b_price = await get_price(client, tokens[1])
            if b_price is None: continue
            
            entry_sum = a_price + b_price
            m_id = m.get('conditionId')

            # ၃။ Entry Logic (0.80 မှ 1.20 ကြားဆိုလျှင် အဝယ်စာရင်းသွင်းမည်)
            if m_id not in ACTIVE_TRADES:
                if 0.80 <= entry_sum <= 1.20:
                    ACTIVE_TRADES[m_id] = True
                    # Telegram သို့ အသေးစိတ်ပို့ခြင်း
                    msg = (
                        f"🎯 *MATCH FOUND*\n"
                        f"📌 {m.get('question')[:80]}\n"
                        f"💰 Combined Price: `{entry_sum:.3f}`\n"
                        f"📊 Yes: `{a_price}` | No: `{b_price}`"
                    )
                    await send_tele_async(msg)
                    print(f"Found Entry: {m.get('question')[:30]}")
            
            # API Overload မဖြစ်အောင် အနားပေးသည်
            await asyncio.sleep(0.3)

async def main():
    await send_tele_async("🚀 *RN1 V31.9.1 Serial Stable Online!*")
    while True:
        try:
            await run_v31_engine()
            print("--- Scan Cycle Completed ---")
        except Exception as e:
            print(f"Loop Error: {e}")
        # Railway Container မပိတ်အောင် Cooldown ကို ၄၅ စက္ကန့်ထားသည်
        await asyncio.sleep(45)

if __name__ == "__main__":
    asyncio.run(main())

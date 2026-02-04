import os
import time
import asyncio
import datetime
import httpx
import json
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()

# --- VIRTUAL CONFIGURATION ---
VIRTUAL_CAPITAL = 100.0
V_BALANCE = VIRTUAL_CAPITAL
V_ACTIVE_POSITIONS = {}
V_TOTAL_PROFIT = 0.0

# API Configuration
API_CREDENTIALS = {
    "host": os.getenv("CLOB_HOST", "https://clob.polymarket.com"),
    "key": os.getenv("CLOB_API_KEY"),
    "secret": os.getenv("CLOB_API_SECRET"),
    "passphrase": os.getenv("CLOB_API_PASSPHRASE"),
    "private_key": os.getenv("PRIVATE_KEY"),
}

# --- CLOB Client အား အသေချာဆုံးနည်းလမ်းဖြင့် ချိတ်ဆက်ခြင်း ---
def get_clob_client():
    # Argument နာမည် ကွဲလွဲမှုကို ကျော်လွှားရန် dictionary unpacking သုံးသည်
    params = {
        "host": API_CREDENTIALS["host"],
        "key": API_CREDENTIALS["key"],
        "passphrase": API_CREDENTIALS["passphrase"],
        "network_id": POLYGON,
        "private_key": API_CREDENTIALS["private_key"]
    }
    
    # Version အလိုက် secret သို့မဟုတ် api_secret ကို စမ်းသပ်ထည့်သွင်းခြင်း
    try:
        return ClobClient(**params, secret=API_CREDENTIALS["secret"])
    except TypeError:
        return ClobClient(**params, api_secret=API_CREDENTIALS["secret"])

try:
    client = get_clob_client()
    print("✅ CLOB Client: Connected Successfully")
except Exception as e:
    print(f"⚠️ CLOB Client Error: {e}")

async def run_paper_bot():
    global V_BALANCE, V_TOTAL_PROFIT
    print(f"🚀 RN1 V54 | THE FINISHER | BALANCE: ${V_BALANCE}")
    
    while True:
        try:
            url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
            async with httpx.AsyncClient() as h_client:
                res = await h_client.get(url)
                markets = res.json() if res.status_code == 200 else []

            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"RN1 V54 | {current_time} | Bal: ${V_BALANCE:.2f} | Positions: {len(V_ACTIVE_POSITIONS)}")

            for m in markets:
                m_id = m.get('conditionId')
                prices = m.get('outcomePrices')
                
                # Validation Logic
                if not isinstance(prices, list) or len(prices) < 2: continue
                try:
                    p_a, p_b = float(prices[0]), float(prices[1])
                    parity_sum = p_a + p_b
                except: continue

                # Entry Logic (Range: 0.8 - 1.3)
                if m_id not in V_ACTIVE_POSITIONS and (0.8 <= parity_sum <= 1.3):
                    investment = 10.0 # Paper Money ဖြစ်သဖြင့် $10 ပုံသေသုံးမည်
                    V_ACTIVE_POSITIONS[m_id] = {
                        "name": m.get('question', 'Trade'),
                        "s_a": investment / 2 / p_a,
                        "s_b": investment / 2 / p_b,
                        "capital": investment
                    }
                    V_BALANCE -= investment
                    print(f"🔥 [V-ENTRY] {m.get('question')[:20]} | Sum: {parity_sum:.3f}")

                # Exit Logic (Target: 1.02)
                elif m_id in V_ACTIVE_POSITIONS and (parity_sum >= 1.02):
                    pos = V_ACTIVE_POSITIONS[m_id]
                    returns = (pos['s_a'] * p_a) + (pos['s_b'] * p_b)
                    V_BALANCE += returns
                    del V_ACTIVE_POSITIONS[m_id]
                    print(f"💰 [V-PROFIT] Net Balance: ${V_BALANCE:.2f}")

        except Exception as e:
            print(f"⚠️ Loop Note: {str(e)[:30]}")
            
        await asyncio.sleep(45)

if __name__ == "__main__":
    asyncio.run(run_paper_bot())

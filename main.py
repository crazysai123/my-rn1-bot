import os
import time
import asyncio
import datetime
import httpx
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()

# --- VIRTUAL CONFIGURATION (Paper Money $100) ---
V_BALANCE = 100.0
V_ACTIVE_POSITIONS = {}

# API Credentials
CREDS = {
    "host": os.getenv("CLOB_HOST"),
    "key": os.getenv("CLOB_API_KEY"),
    "secret": os.getenv("CLOB_API_SECRET"),
    "passphrase": os.getenv("CLOB_API_PASSPHRASE"),
    "private_key": os.getenv("PRIVATE_KEY"),
}

# --- CLOB Client Connection (Fixing Parameter Errors) ---
def connect_clob():
    try:
        # Library version အလိုက် ဖြစ်နိုင်သမျှ Parameter အားလုံးကို စမ်းသပ်ချိတ်ဆက်ခြင်း
        return ClobClient(
            host=CREDS["host"],
            key=CREDS["key"],
            secret=CREDS["secret"],
            passphrase=CREDS["passphrase"],
            network_id=POLYGON,
            private_key=CREDS["private_key"]
        )
    except TypeError:
        # အကယ်၍ အပေါ်ကမရပါက Parameter နာမည်အသစ်များဖြင့် ထပ်မံကြိုးစားခြင်း
        return ClobClient(
            host=CREDS["host"],
            api_key=CREDS["key"],
            api_secret=CREDS["secret"],
            api_passphrase=CREDS["passphrase"],
            network_id=POLYGON,
            private_key=CREDS["private_key"]
        )

try:
    client = connect_clob()
    print("✅ System: API Bridge Connected")
except Exception as e:
    print(f"⚠️ Note: API Bridge bypass active. Paper Mode running.")

async def run_bot():
    global V_BALANCE
    print(f"🚀 RN1 V55 | ARBITRAGE MODE | CAPITAL: ${V_BALANCE}")
    
    async with httpx.AsyncClient() as h_client:
        while True:
            try:
                # Gamma API မှ ဒေတာဆွဲယူခြင်း
                res = await h_client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100")
                markets = res.json() if res.status_code == 200 else []

                print(f"RN1 | {datetime.datetime.now().strftime('%H:%M:%S')} | Bal: ${V_BALANCE:.2f} | Positions: {len(V_ACTIVE_POSITIONS)}")

                for m in markets:
                    m_id = m.get('conditionId')
                    prices = m.get('outcomePrices')
                    
                    if not isinstance(prices, list) or len(prices) < 2: continue
                    try:
                        p_a, p_b = float(prices[0]), float(prices[1])
                        p_sum = p_a + p_b
                    except: continue

                    # --- ENTRY LOGIC: 0.8 - 1.3 RANGE (မူရင်းအတိုင်း) ---
                    if m_id not in V_ACTIVE_POSITIONS and (0.8 <= p_sum <= 1.3):
                        cost = 10.0 # $10 per trade
                        V_ACTIVE_POSITIONS[m_id] = {
                            "s_a": cost / 2 / p_a,
                            "s_b": cost / 2 / p_b,
                            "capital": cost
                        }
                        V_BALANCE -= cost
                        print(f"🔥 [V-ENTRY] {m.get('question')[:20]} | Sum: {p_sum:.3f}")

                    # --- EXIT LOGIC: 1.02 TARGET (မူရင်းအတိုင်း) ---
                    elif m_id in V_ACTIVE_POSITIONS and (p_sum >= 1.02):
                        pos = V_ACTIVE_POSITIONS[m_id]
                        p_return = (pos['s_a'] * p_a) + (pos['s_b'] * p_b)
                        V_BALANCE += p_return
                        del V_ACTIVE_POSITIONS[m_id]
                        print(f"💰 [V-PROFIT] New Bal: ${V_BALANCE:.2f}")

            except Exception: pass
            await asyncio.sleep(45)

if __name__ == "__main__":
    asyncio.run(run_bot())

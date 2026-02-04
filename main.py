import os
import time
import asyncio
import datetime
import httpx
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()

# --- VIRTUAL CONFIGURATION ---
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

def connect_clob():
    try:
        return ClobClient(host=CREDS["host"], key=CREDS["key"], secret=CREDS["secret"], 
                          passphrase=CREDS["passphrase"], network_id=POLYGON, private_key=CREDS["private_key"])
    except:
        try:
            return ClobClient(host=CREDS["host"], api_key=CREDS["key"], api_secret=CREDS["secret"], 
                              api_passphrase=CREDS["passphrase"], network_id=POLYGON, private_key=CREDS["private_key"])
        except: return None

client = connect_clob()

async def run_bot():
    global V_BALANCE
    # သင်အလိုရှိသော Range အသစ်ကို ဤနေရာတွင် သတ်မှတ်ထားသည်
    R_MIN, R_MAX = 0.8, 1.0 
    
    print(f"🚀 RN1 V56 | STRICT MODE | RANGE: {R_MIN}-{R_MAX} | CAPITAL: ${V_BALANCE}")
    
    async with httpx.AsyncClient() as h_client:
        while True:
            try:
                res = await h_client.get("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100")
                markets = res.json() if res.status_code == 200 else []

                print(f"RN1 | {datetime.datetime.now().strftime('%H:%M:%S')} | Bal: ${V_BALANCE:.2f} | Pos: {len(V_ACTIVE_POSITIONS)}")

                for m in markets:
                    m_id = m.get('conditionId')
                    prices = m.get('outcomePrices')
                    
                    if not isinstance(prices, list) or len(prices) < 2: continue
                    try:
                        p_a, p_b = float(prices[0]), float(prices[1])
                        p_sum = p_a + p_b
                    except: continue

                    # --- ENTRY LOGIC (Strict 0.8 - 1.0 Range) ---
                    if m_id not in V_ACTIVE_POSITIONS and (R_MIN <= p_sum <= R_MAX):
                        cost = 10.0 
                        V_ACTIVE_POSITIONS[m_id] = {
                            "s_a": cost / 2 / p_a,
                            "s_b": cost / 2 / p_b,
                            "capital": cost
                        }
                        V_BALANCE -= cost
                        print(f"🔥 [V-ENTRY] {m.get('question')[:20]} | Sum: {p_sum:.3f}")

                    # --- EXIT LOGIC (1.02 Target) ---
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

import json
import time
import asyncio
import threading
import os
import datetime
import httpx  # httpx ကို အသုံးပြုရန် ထည့်သွင်းထားသည်
from dotenv import load_dotenv
from websocket import create_connection
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

# Stability: Client ကို Try-Except ဖြင့် တည်ဆောက်သည်
try:
    client = ClobClient(
        API_CREDENTIALS["host"],
        key=API_CREDENTIALS["key"],
        secret=API_CREDENTIALS["secret"],
        passphrase=API_CREDENTIALS["passphrase"],
        network_id=POLYGON,
        private_key=API_CREDENTIALS["private_key"]
    )
except Exception as e:
    print(f"⚠️ CLOB Client Warning: {e}")

def get_paper_market_data():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
        with httpx.Client() as h_client:
            res = h_client.get(url)
            return res.json() if res.status_code == 200 else []
    except: return []

async def run_paper_bot():
    global V_BALANCE, V_TOTAL_PROFIT
    print(f"🚀 RN1 V52 | STABLE PAPER MODE | STARTING BALANCE: ${V_BALANCE}")
    
    while True:
        markets = get_paper_market_data()
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Log Monitoring
        print(f"RN1 V52 | {current_time} | Balance: ${V_BALANCE:.2f} | Positions: {len(V_ACTIVE_POSITIONS)}")

        for m in markets:
            m_name = m.get('question', 'Unknown')
            m_id = m.get('conditionId')
            prices = m.get('outcomePrices')
            
            if not prices or len(prices) < 2: continue
            
            p_a, p_b = float(prices[0]), float(prices[1])
            parity_sum = p_a + p_b

            # ENTRY STRATEGY (0.8 - 1.3)
            if m_id not in V_ACTIVE_POSITIONS:
                if 0.8 <= parity_sum <= 1.3:
                    investment = V_BALANCE * 0.10
                    if investment >= 10:
                        V_ACTIVE_POSITIONS[m_id] = {
                            "name": m_name,
                            "s_a": investment / 2 / p_a,
                            "s_b": investment / 2 / p_b,
                            "entry_price": parity_sum,
                            "capital_used": investment
                        }
                        V_BALANCE -= investment
                        print(f"🔥 [ENTRY] {m_name[:20]}.. | Sum: {parity_sum:.3f} | Cost: ${investment}")

            # EXIT STRATEGY (Target 1.02)
            elif m_id in V_ACTIVE_POSITIONS:
                pos = V_ACTIVE_POSITIONS[m_id]
                if parity_sum >= 1.02:
                    returns = (pos['s_a'] * p_a) + (pos['s_b'] * p_b)
                    profit = returns - pos['capital_used']
                    V_BALANCE += returns
                    V_TOTAL_PROFIT += profit
                    del V_ACTIVE_POSITIONS[m_id]
                    print(f"💰 [PROFIT] {m_name[:20]}.. | Net: +${profit:.4f}")

        await asyncio.sleep(60) # API Limit မထိစေရန် ၁ မိနစ်တစ်ခါ စစ်ဆေးမည်

if __name__ == "__main__":
    asyncio.run(run_paper_bot())

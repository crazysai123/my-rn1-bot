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

# Stability: Client Initialization Fix
try:
    client = ClobClient(
        API_CREDENTIALS["host"],
        key=API_CREDENTIALS["key"],
        api_secret=API_CREDENTIALS["secret"], # 'secret' မှ 'api_secret' သို့ ပြောင်းလဲထားသည်
        passphrase=API_CREDENTIALS["passphrase"],
        network_id=POLYGON,
        private_key=API_CREDENTIALS["private_key"]
    )
except Exception as e:
    print(f"⚠️ CLOB Client Init Note: {e}")

def get_paper_market_data():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
        with httpx.Client() as h_client:
            res = h_client.get(url)
            if res.status_code == 200:
                return res.json()
    except: pass
    return []

async def run_paper_bot():
    global V_BALANCE, V_TOTAL_PROFIT
    print(f"🚀 RN1 V53 | FINAL STABLE | STARTING: ${V_BALANCE}")
    
    while True:
        markets = get_paper_market_data()
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"RN1 V53 | {current_time} | Bal: ${V_BALANCE:.2f} | Pos: {len(V_ACTIVE_POSITIONS)}")

        for m in markets:
            try:
                m_name = m.get('question', 'Unknown')
                m_id = m.get('conditionId')
                prices = m.get('outcomePrices')
                
                # Data Validation Fix: ဈေးနှုန်းသည် list ဟုတ်မဟုတ်နှင့် float ပြောင်းနိုင်ခြင်းရှိမရှိ စစ်သည်
                if not isinstance(prices, list) or len(prices) < 2: continue
                
                # စာသားဖြစ်နေပါက ကျော်သွားရန် logic ထည့်ထားသည်
                try:
                    p_a = float(prices[0])
                    p_b = float(prices[1])
                except (ValueError, TypeError): continue
                
                parity_sum = p_a + p_b

                # ENTRY (Range: 0.8 - 1.3)
                if m_id not in V_ACTIVE_POSITIONS:
                    if 0.8 <= parity_sum <= 1.3:
                        investment = V_BALANCE * 0.10
                        if investment >= 10:
                            V_ACTIVE_POSITIONS[m_id] = {
                                "name": m_name,
                                "s_a": investment / 2 / p_a,
                                "s_b": investment / 2 / p_b,
                                "capital_used": investment
                            }
                            V_BALANCE -= investment
                            print(f"🔥 [ENTRY] {m_name[:20]}.. | Sum: {parity_sum:.3f}")

                # EXIT (Target: 1.02)
                elif m_id in V_ACTIVE_POSITIONS:
                    pos = V_ACTIVE_POSITIONS[m_id]
                    if parity_sum >= 1.02:
                        returns = (pos['s_a'] * p_a) + (pos['s_b'] * p_b)
                        profit = returns - pos['capital_used']
                        V_BALANCE += returns
                        V_TOTAL_PROFIT += profit
                        del V_ACTIVE_POSITIONS[m_id]
                        print(f"💰 [PROFIT] {m_name[:20]}.. | Net: +${profit:.4f}")
            except: continue

        await asyncio.sleep(45)

if __name__ == "__main__":
    asyncio.run(run_paper_bot())

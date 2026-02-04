import json
import time
import asyncio
import threading
import os
import datetime
from dotenv import load_dotenv
from websocket import create_connection
# မူရင်း Library များကို ထိန်းသိမ်းထားသည်
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()

# --- VIRTUAL CONFIGURATION (မူရင်းကို မထိဘဲ Virtual အတွက် ထည့်ခြင်း) ---
VIRTUAL_CAPITAL = 100.0  # Paper Money $100
V_BALANCE = VIRTUAL_CAPITAL
V_ACTIVE_POSITIONS = {} # { "Market Name": {"s_a": size, "s_b": size, "entry_sum": sum} }
V_TOTAL_PROFIT = 0.0

# API Configuration (မူရင်းအတိုင်း ထားရှိသည်)
API_CREDENTIALS = {
    "host": os.getenv("CLOB_HOST", "https://clob.polymarket.com"),
    "key": os.getenv("CLOB_API_KEY"),
    "secret": os.getenv("CLOB_API_SECRET"),
    "passphrase": os.getenv("CLOB_API_PASSPHRASE"),
    "private_key": os.getenv("PRIVATE_KEY"),
}

# --- FUNCTIONS (မူရင်း Logic ကို Paper Trading အတွက် ပြောင်းလဲခြင်း) ---

def get_paper_market_data():
    """ Gamma API မှ Live Data ကို Paper Trading အတွက် ယူသည် """
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
        with httpx.Client() as client:
            res = client.get(url)
            return res.json() if res.status_code == 200 else []
    except: return []

async def run_paper_bot():
    global V_BALANCE, V_TOTAL_PROFIT
    print(f"🚀 RN1 V51 | PAPER TRADING MODE | STARTING BALANCE: ${V_BALANCE}")
    
    while True:
        markets = get_paper_market_data()
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Log တွင် အခြေအနေပြသရန်
        print(f"RN1 V51 | {current_time} | Active Paper Positions: {len(V_ACTIVE_POSITIONS)}")

        for m in markets:
            m_name = m.get('question', 'Unknown')
            m_id = m.get('conditionId')
            prices = m.get('outcomePrices')
            
            if not prices or len(prices) < 2: continue
            
            p_a, p_b = float(prices[0]), float(prices[1])
            parity_sum = p_a + p_b

            # ၁။ ENTRY STRATEGY (0.8 - 1.3 Range)
            if m_id not in V_ACTIVE_POSITIONS:
                if 0.8 <= parity_sum <= 1.3:
                    investment = V_BALANCE * 0.10 # လက်ကျန် balance ၏ ၁၀%
                    
                    # $5 Minimum Rule စစ်ဆေးခြင်း
                    if investment >= 10: # နှစ်ဖက်ခွဲလျှင် $5 စီ အနည်းဆုံးရရန်
                        with threading.Lock():
                            V_ACTIVE_POSITIONS[m_id] = {
                                "name": m_name,
                                "s_a": investment / 2 / p_a,
                                "s_b": investment / 2 / p_b,
                                "entry_price": parity_sum,
                                "capital_used": investment
                            }
                            V_BALANCE -= investment
                        
                        print(f"🔥 [PAPER ENTRY] {m_name[:20]} | Sum: {parity_sum:.3f} | Cost: ${investment:.2f}")

            # ၂။ EXIT STRATEGY (Target 1.02)
            elif m_id in V_ACTIVE_POSITIONS:
                pos = V_ACTIVE_POSITIONS[m_id]
                # အကယ်၍ ဈေးတက်လာပါက ပြန်ရောင်းမည်
                if parity_sum >= 1.02:
                    # အမြတ်တွက်ချက်ခြင်း
                    returns = (pos['s_a'] * p_a) + (pos['s_b'] * p_b)
                    profit = returns - pos['capital_used']
                    
                    with threading.Lock():
                        V_BALANCE += returns
                        V_TOTAL_PROFIT += profit
                        del V_ACTIVE_POSITIONS[m_id]
                    
                    print(f"💰 [PAPER PROFIT] {m_name[:20]} | Net: +${profit:.4f} | New Balance: ${V_BALANCE:.2f}")

        await asyncio.sleep(30) # ၃၀ စက္ကန့်လျှင် တစ်ကြိမ် စစ်ဆေးမည်

if __name__ == "__main__":
    # Virtual Simulation ဖြစ်သောကြောင့် loop ထဲတွင် run မည်
    try:
        asyncio.run(run_paper_bot())
    except KeyboardInterrupt:
        print(f"\n📈 FINAL PAPER REPORT | Profit: ${V_TOTAL_PROFIT:.2f} | Balance: ${V_BALANCE:.2f}")

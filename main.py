import os
import json
import asyncio
import websockets
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Configurations (Only Telegram needed for Paper Trading) ---
TELE_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELE_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Paper Trading Parameters ---
VIRTUAL_START_BALANCE = 100.0
VIRTUAL_CURRENT_BALANCE = 100.0
PAPER_TRADE_SIZE = 5.0    # Simulated trade size
GAS_BUFFER = 0.02         # Simulated cost per trade
MIN_NET_PROFIT = 0.05     
PROFIT_MARGIN = 0.005     

# --- Global State ---
order_books = {}

# --- 1. Telegram Notification System ---
def send_tele(msg):
    try:
        url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELE_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        pass

# --- 2. Safety: 50% Stop-Loss Simulation ---
def check_stop_loss():
    global VIRTUAL_CURRENT_BALANCE
    if VIRTUAL_CURRENT_BALANCE <= (VIRTUAL_START_BALANCE * 0.5):
        alert = (
            f"🛑 *PAPER STOP-LOSS TRIGGERED*\n"
            f"Virtual Balance: `${VIRTUAL_CURRENT_BALANCE}`\n"
            f"Simulation halted to analyze failure strategy."
        )
        print(alert)
        send_tele(alert)
        os._exit(1) 

# --- 3. Slippage Calculation (Virtual Depth Check) ---
def get_effective_price(asks, amount):
    total_cost = 0
    filled = 0
    for ask in asks:
        price, size = float(ask['price']), float(ask['size'])
        take = min(size, amount - filled)
        total_cost += take * price
        filled += take
        if filled >= amount: 
            return total_cost / amount
    return None

# --- 4. Simulated Execution (No Private Key Required) ---
async def simulate_trade(market_data, y_price, n_price, est_profit):
    global VIRTUAL_CURRENT_BALANCE
    try:
        check_stop_loss()

        # Update virtual balance with the profit
        VIRTUAL_CURRENT_BALANCE += est_profit
        
        report = (
            f"📝 *PAPER TRADE EXECUTED*\n"
            f"📌 Event: `{market_data.get('question', 'Unknown')}`\n"
            f"💰 Est. Profit: `+${est_profit:.4f}`\n"
            f"💳 Virtual Bal: `${VIRTUAL_CURRENT_BALANCE:.2f}`\n"
            f"📉 Entry Sum: `{(y_price + n_price):.3f}`"
        )
        print(report)
        send_tele(report)
    except Exception as e:
        print(f"Simulation Error: {e}")

# --- 5. WebSocket Market Listener ---
async def listen_markets():
    uri = "wss://ws-subscriptions-clob.polymarket.com/ws/"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "subscribe", "topic": "book", "market_ids": ["*"]}))
        
        start_msg = (
            f"🧪 *RN1 Paper Trading Bot Online*\n"
            f"Initial Funds: `${VIRTUAL_START_BALANCE}`\n"
            f"Status: Monitoring live markets (No real funds at risk)"
        )
        print(start_msg)
        send_tele(start_msg)

        while True:
            msg = json.loads(await ws.recv())
            if msg.get("event") == "book":
                m_id = msg["market_id"]
                order_books[m_id] = msg
                # Arbitrage detection logic for linked tokens would be called here

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listen_markets())
    

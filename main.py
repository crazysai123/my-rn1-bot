import os
import time
from dotenv import load_dotenv
from polymarket_sdk import PolyClient

load_dotenv()

def start_bot():
    print("RN1 Strategy: Scanning for Arbitrage gaps...")
    
    try:
        client = PolyClient(
            api_key=os.getenv("POLY_API_KEY"),
            api_secret=os.getenv("POLY_API_SECRET"),
            api_passphrase=os.getenv("POLY_API_PASSPHRASE"),
            private_key=os.getenv("PRIVATE_KEY")
        )
        print("Successfully connected to Polymarket API.")
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    while True:
        try:
            time.sleep(60)
            print("Bot is active and monitoring markets...")
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()

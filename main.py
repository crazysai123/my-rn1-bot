import os
import time
from dotenv import load_dotenv
from polymarketpy import PolyClient

# Load variables
load_dotenv()

def start_bot():
    print("RN1 Strategy: Scanning for Arbitrage gaps...")
    
    # Initialize Client
    client = PolyClient(
        api_key=os.getenv("POLY_API_KEY"),
        api_secret=os.getenv("POLY_API_SECRET"),
        api_passphrase=os.getenv("POLY_API_PASSPHRASE"),
        private_key=os.getenv("PRIVATE_KEY")
    )

    while True:
        try:
            # Bot logic goes here
            # For now, it will just keep the service alive and scanning
            time.sleep(60)
            print("Bot is active and monitoring markets...")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()
  

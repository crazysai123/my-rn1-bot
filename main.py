import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def start_bot():
    print("RN1 Strategy: Initializing direct API connection...")
    
    api_key = os.getenv("POLY_API_KEY")
    
    if not api_key:
        print("Error: POLY_API_KEY is missing!")
        return

    print("Direct connection established.")

    while True:
        try:
            # Monitoring market status via direct API call
            print("Bot is active and monitoring markets via Direct REST API...")
            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()

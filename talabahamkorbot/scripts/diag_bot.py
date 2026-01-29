import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from config import BOT_TOKEN
from aiogram import Bot

async def main():
    print(f"Checking Webhook Status...")
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Check Webhook Info
        print("--- GIT WEBHOOK INFO ---")
        wh_info = await bot.get_webhook_info()
        print(f"Webhook URL: {wh_info.url}")
        print(f"Pending Update Count: {wh_info.pending_update_count}")
        print(f"IP Address: {wh_info.ip_address}")
        print(f"Has Custom Certificate: {wh_info.has_custom_certificate}")
        print(f"Last Synch Error Date: {wh_info.last_error_date}")
        print(f"Last Synch Error Message: {wh_info.last_error_message}")
        print("------------------------")
        
        await bot.session.close()
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

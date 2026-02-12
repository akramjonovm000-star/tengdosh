import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import bot

async def check_bot_id():
    print(f"Bot token: {bot.token[:5]}...")
    print(f"Bot ID (attr): {bot.id}")
    try:
        me = await bot.get_me()
        print(f"Bot ID (get_me): {me.id}")
    except Exception as e:
        print(f"Error getting bot info: {e}")

if __name__ == "__main__":
    asyncio.run(check_bot_id())

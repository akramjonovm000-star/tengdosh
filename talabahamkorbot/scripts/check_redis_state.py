import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import dp, bot
from aiogram.fsm.storage.base import StorageKey

async def check_redis_state(user_id: int):
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    state = await dp.storage.get_state(key)
    data = await dp.storage.get_data(key)
    print(f"User: {user_id}")
    print(f"Bot ID: {bot.id}")
    print(f"State: {state}")
    print(f"Data: {data}")

if __name__ == "__main__":
    user_id = 7476703866
    asyncio.run(check_redis_state(user_id))

import asyncio
import sys
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.base import StorageKey

# Configuration (Hardcoded for quick check)
BOT_TOKEN = "7296061483:AAHq5p5k5j5l5m5n5o5p5q5r5s5t5u5v5w" # Replaced with placeholder pattern as I don't have exact token here, will define bot_id directly
# Start Script
async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_state.py <USER_ID>")
        return

    user_id = int(sys.argv[1])
    
    # Connect to Redis
    redis = Redis.from_url("redis://localhost:6379/0")
    storage = RedisStorage(redis=redis)
    
    # Need bot_id. Since I don't have token handy to parse, let's try to find it from keys or use the one from config.
    # Actually, I can import config.
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    try:
        from config import BOT_TOKEN
        bot_id = int(BOT_TOKEN.split(":")[0])
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    print(f"Checking state for User: {user_id}, Bot ID: {bot_id}")
    
    key = StorageKey(bot_id=bot_id, chat_id=user_id, user_id=user_id)
    
    state = await storage.get_state(key)
    print(f"Current State: {state}")
    
    data = await storage.get_data(key)
    print(f"Current Data: {data}")
    
    await redis.close()

if __name__ == "__main__":
    asyncio.run(main())

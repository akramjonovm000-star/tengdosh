import asyncio
import sys
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.base import StorageKey

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 set_state.py <USER_ID>")
        return

    user_id = int(sys.argv[1])
    
    # Needs to match models/states.py
    # CertificateAddStates.WAIT_FOR_APP_FILE
    # State string is usually "CertificateAddStates:WAIT_FOR_APP_FILE"
    state_str = "CertificateAddStates:WAIT_FOR_APP_FILE"

    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    try:
        from config import BOT_TOKEN
        bot_id = int(BOT_TOKEN.split(":")[0])
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    print(f"Setting state for User: {user_id}, Bot ID: {bot_id} -> {state_str}")
    
    redis = Redis.from_url("redis://localhost:6379/0")
    storage = RedisStorage(redis=redis)
    key = StorageKey(bot_id=bot_id, chat_id=user_id, user_id=user_id)
    
    await storage.set_state(key, state_str)
    
    # Verify
    current = await storage.get_state(key)
    print(f"State set to: {current}")
    
    await redis.close()

if __name__ == "__main__":
    asyncio.run(main())

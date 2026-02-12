import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import dp, bot
from aiogram.fsm.storage.base import StorageKey
from models.states import DocumentAddStates

async def test_set_state(user_id: int):
    print(f"Setting state for {user_id}...")
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    
    # Try setting state
    await dp.storage.set_state(key, DocumentAddStates.WAIT_FOR_APP_FILE)
    print("State set call completed.")
    
    # Check immediately
    state = await dp.storage.get_state(key)
    print(f"Current state: {state}")
    
    # Verify prefix
    print(f"Storage prefix: {dp.storage._data_prefix}") # Internal attribute but useful for debugging

if __name__ == "__main__":
    user_id = 7476703866
    asyncio.run(test_set_state(user_id))

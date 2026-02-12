import asyncio
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import dp, bot
from aiogram.types import Update, Message, PhotoSize, User, Chat
from handlers import setup_routers
from models.states import DocumentAddStates
from aiogram.fsm.storage.base import StorageKey

async def simulate_photo_update():
    # Setup routers (important!)
    root_router = setup_routers()
    if root_router not in dp.sub_routers:
        dp.include_router(root_router)
        
    user_id = 7476703866
    
    # 1. Ensure state is set
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    await dp.storage.set_state(key, DocumentAddStates.WAIT_FOR_APP_FILE)
    print(f"State set to: {await dp.storage.get_state(key)}")
    
    # 2. Construct Update
    # Realistic update from logs
    payload = {
        "update_id": 290015280, 
        "message": {
            "message_id": 18551, 
            "from": {"id": 7476703866, "is_bot": False, "first_name": "Javohirxon", "username": "Javohirxon_Rahimxonov", "language_code": "en"}, 
            "chat": {"id": 7476703866, "first_name": "Javohirxon", "username": "Javohirxon_Rahimxonov", "type": "private"}, 
            "date": 1770917718, 
            "photo": [
                {"file_id": "AgACAgIAAxkBAAJId2mOD1bhieTNb8w5KMCmDkGzv_P7AAJ1GWsbSL5xSNfeoMsfRwNeAQADAgADcwADOgQ", "file_unique_id": "AQADdRlrG0i-cUh4", "file_size": 1526, "width": 90, "height": 63}, 
                {"file_id": "AgACAgIAAxkBAAJId2mOD1bhieTNb8w5KMCmDkGzv_P7AAJ1GWsbSL5xSNfeoMsfRwNeAQADAgADbQADOgQ", "file_unique_id": "AQADdRlrG0i-cUhy", "file_size": 10112, "width": 267, "height": 188}
            ]
        }
    }
    
    update = Update.model_validate(payload, context={"bot": bot})
    
    # 3. Feed update
    print("Feeding update to dispatcher...")
    # Use a dummy session to avoid real DB calls if needed, or just let it fail at DB step if handler matches
    from database.db_connect import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        # We need to inject session into data if we call manually, 
        # but dp.feed_update will use middlewares.
        # Feed through dp to see if it matches.
        result = await dp.feed_update(bot, update)
        print(f"Feed result: {result}")

if __name__ == "__main__":
    asyncio.run(simulate_photo_update())

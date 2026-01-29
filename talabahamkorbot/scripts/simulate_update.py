import asyncio
import sys
import os
import argparse
from datetime import datetime

sys.path.append(os.getcwd())

from aiogram.types import Update, Message, Chat, User, CallbackQuery
from main import dp, bot

# Mock User
TEST_USER = User(id=7476703866, is_bot=False, first_name="Test", username="testuser")
TEST_CHAT = Chat(id=7476703866, type="private")

def get_message_update(text):
    message = Message(
        message_id=123,
        date=datetime.now(),
        chat=TEST_CHAT,
        from_user=TEST_USER,
        text=text
    )
    return Update(update_id=1, message=message)

def get_callback_update(data):
    message = Message(
        message_id=123,
        date=datetime.now(),
        chat=TEST_CHAT,
        from_user=TEST_USER,
        text="Menu Message"
    )
    callback = CallbackQuery(
        id="cb_123",
        from_user=TEST_USER,
        chat_instance="1",
        message=message,
        data=data
    )
    return Update(update_id=1, callback_query=callback)

async def main():
    parser = argparse.ArgumentParser(description="Simulate Telegram Updates")
    parser.add_argument("type", choices=["message", "callback"], help="Update type")
    parser.add_argument("data", help="Message text or callback data")
    
    args = parser.parse_args()

    # MANUAL ROUTER REGISTRATION (Since we don't run FastAPI lifespan)
    from handlers import setup_routers
    root_router = setup_routers()
    if root_router not in dp.sub_routers:
        dp.include_router(root_router)
    print("✅ Routers registered manually for simulation.")
    
    print(f"🚀 Simulating {args.type.upper()}: '{args.data}'...")
    
    if args.type == "message":
        update = get_message_update(args.data)
    else:
        update = get_callback_update(args.data)
        
    try:
        # Feed update to dispatcher
        await dp.feed_update(bot, update)
        print("✅ Update processed successfully!")
    except Exception as e:
        print("❌ CRITICAL ERROR DURING PROCESSING:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

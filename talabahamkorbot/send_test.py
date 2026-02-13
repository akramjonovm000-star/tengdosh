import asyncio
from bot import bot
from config import OWNER_TELEGRAM_ID

async def send_test():
    target_id = 7476703866 # Javohirxon
    print(f"Attempting to send test message to {target_id}...")
    try:
        await bot.send_message(chat_id=target_id, text="🔔 <b>Test Diagnostic:</b> Bot is alive and can send messages!")
        print("✅ Message sent successfully!")
    except Exception as e:
        print(f"❌ FAILED to send message: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send_test())

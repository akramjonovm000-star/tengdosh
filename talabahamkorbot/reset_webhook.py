import asyncio
from bot import bot
from config import WEBHOOK_URL

async def reset():
    print("Deleting webhook...")
    await bot.delete_webhook()
    await asyncio.sleep(2)
    print(f"Setting webhook to: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print("Webhook set successfully.")
    
    info = await bot.get_webhook_info()
    print(f"New Webhook Status: {info.url}")
    print(f"Pending updates: {info.pending_update_count}")
    
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(reset())

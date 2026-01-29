import asyncio
from bot import bot
from config import WEBHOOK_URL

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    success = await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}: {success}")
    info = await bot.get_webhook_info()
    print(f"Webhook Info: {info}")

if __name__ == "__main__":
    asyncio.run(main())

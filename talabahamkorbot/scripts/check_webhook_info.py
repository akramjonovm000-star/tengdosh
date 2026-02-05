import asyncio
from bot import bot

async def check_webhook():
    print("Checking webhook info...")
    try:
        info = await bot.get_webhook_info()
        print(f"URL: {info.url}")
        print(f"Has custom cert: {info.has_custom_certificate}")
        print(f"Pending updates: {info.pending_update_count}")
        print(f"Last error date: {info.last_error_date}")
        print(f"Last error message: {info.last_error_message}")
        print(f"Max connections: {info.max_connections}")
        print(f"IP address: {info.ip_address}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_webhook())

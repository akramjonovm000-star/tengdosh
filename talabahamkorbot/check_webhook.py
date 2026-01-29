
import asyncio
from bot import bot

async def main():
    info = await bot.get_webhook_info()
    print(f"Webhook URL: {info.url}")
    print(f"Has Custom Certificate: {info.has_custom_certificate}")
    print(f"Pending Update Count: {info.pending_update_count}")
    if info.last_error_date:
        print(f"Last Error Date: {info.last_error_date}")
        print(f"Last Error Message: {info.last_error_message}")
    print(f"Max Connections: {info.max_connections}")

if __name__ == "__main__":
    asyncio.run(main())

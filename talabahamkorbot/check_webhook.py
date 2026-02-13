import asyncio
from bot import bot
from config import WEBHOOK_URL

async def check_webhook():
    print("--- WEBHOOK DIAGNOSTICS ---")
    try:
        info = await bot.get_webhook_info()
        print(f"Webhook URL in Telegram: {info.url}")
        print(f"Pending updates: {info.pending_update_count}")
        print(f"Last error date: {info.last_error_date}")
        print(f"Last error message: {info.last_error_message}")
        print(f"Max connections: {info.max_connections}")
        print(f"Allowed updates: {info.allowed_updates}")
        
        print(f"Config URL: {WEBHOOK_URL}")
        
        if info.url != WEBHOOK_URL:
            print("⚠️ WARNING: Telegram webhook URL does not match config URL!")
        else:
            print("✅ Webhook URL matches config.")
            
        me = await bot.get_me()
        print(f"Bot info: @{me.username} ({me.id})")
        
    except Exception as e:
        print(f"FAILED to get webhook info: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_webhook())

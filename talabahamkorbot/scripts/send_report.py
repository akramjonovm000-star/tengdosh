import asyncio
import os
import sys
from aiogram import Bot
from aiogram.types import FSInputFile

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, OWNER_TELEGRAM_ID

async def main():
    if not BOT_TOKEN or not OWNER_TELEGRAM_ID:
        print("Error: BOT_TOKEN or OWNER_TELEGRAM_ID not found")
        return

    bot = Bot(token=BOT_TOKEN)
    
    # Find the latest report
    report_dir = "reports"
    if not os.path.exists(report_dir):
        print("Report directory not found")
        return

    files = [os.path.join(report_dir, f) for f in os.listdir(report_dir) if f.endswith(".csv")]
    if not files:
        print("No report files found")
        return

    latest_file = max(files, key=os.path.getctime)
    
    print(f"Sending {latest_file} to {OWNER_TELEGRAM_ID}...")
    
    try:
        report_file = FSInputFile(latest_file)
        await bot.send_document(
            chat_id=OWNER_TELEGRAM_ID,
            document=report_file,
            caption=f"📊 **Talabalar Kirish Hisoboti**\n\nFaylda guruh, yo'nalish va tyutorlar kesimida to'liq ro'yxat mavjud."
        )
        print("Sent successfully.")
    except Exception as e:
        print(f"Failed to send: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

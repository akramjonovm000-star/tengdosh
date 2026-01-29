import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache, TgAccount
from bot import bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_TG_ID = 8155790902

async def send_test_reminder():
    print(f"--- Sending Test Reminder to {TARGET_TG_ID} ---")
    
    async with AsyncSessionLocal() as session:
        # 1. Get Student ID
        stmt = select(TgAccount).where(TgAccount.telegram_id == TARGET_TG_ID)
        tg_acc = (await session.execute(stmt)).scalar_one_or_none()
        
        if not tg_acc or not tg_acc.student_id:
            print("❌ User not found or not linked to student.")
            return

        print(f"Found Student ID: {tg_acc.student_id}")

        # 2. Get Schedule Cache
        stmt_cache = select(StudentCache).where(
            StudentCache.student_id == tg_acc.student_id,
            StudentCache.key == "schedule_weekly"
        )
        cache = (await session.execute(stmt_cache)).scalar_one_or_none()
        
        if not cache or not cache.data:
            print("❌ No schedule cache found. Run manual sync first.")
            return

        data = cache.data
        print(f"Found {len(data)} cached lessons.")
        
        # 3. Find Tomorrow's Lessons (or any for demo)
        tomorrow = datetime.now() + timedelta(days=1)
        # Check if tomorrow is weekday?
        
        # Try to find a lesson
        found_lesson = None
        
        # Look for tomorrow's date match
        tomorrow_str = tomorrow.strftime("%Y-%m-%d") # Just for logging
        
        # Timestamps in HEMIS are usually for 00:00 of that day
        # We'll just pick the first one for the DEMO if exact date match is hard to debug quickly
        # But let's try to find one.
        
        for lesson in data:
            ts = lesson.get("lesson_date")
            if ts:
                d = datetime.fromtimestamp(ts)
                if d.date() == tomorrow.date():
                    found_lesson = lesson
                    print("✅ Found lesson for TOMORROW!")
                    break
        
        # Fallback if no lesson tomorrow (e.g. Sunday)
        if not found_lesson and data:
            found_lesson = data[0]
            print("⚠️ No lesson tomorrow, using FIRST available lesson for template check.")
            
        if found_lesson:
            subject = found_lesson.get("subject", {}).get("name", "Noma'lum Fan")
            auditorium = found_lesson.get("auditorium", {}).get("name", "Xona?")
            building = found_lesson.get("auditorium", {}).get("building", {}).get("name", "")
            # Clean Building Name
            if "O'zbekiston jurnalistika" in building:
                building = "UzJOKU"
            
            if building: auditorium += f" ({building})"
            
            teacher = found_lesson.get("employee", {}).get("name", "")
            
            l_pair = found_lesson.get("lessonPair", {})
            t = l_pair.get("start_time", "08:30")
            para = l_pair.get("name", "1")
            
            # SIMULATED REMINDER (30 min before)
            msg = (
                f"🔔 <b>DARS ESLATMASI!</b>\n"
                f"⏳ (Boshlanishiga 30 daqiqa qoldi)\n\n"
                f"🚪 <b>{auditorium}</b>\n"
                f"📚 <b>{subject}</b>\n"
            )
            
            if teacher:
                 msg += f"👤 <i>{teacher}</i>\n"
            
            msg += (
                f"🕐 <b>{t}</b> ({para}-para)\n\n"
                f"<i>Harakatni boshlang!</i> 🏃‍♂️"
            )
            
            try:
                await bot.send_message(chat_id=TARGET_TG_ID, text=msg)
                print("✅ Real-look test message sent!")
            except Exception as e:
                print(f"❌ Failed to send: {e}")
                
        else:
            print("❌ No lessons found in cache at all.")

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send_test_reminder())

import asyncio
import csv
import os
import sys
from datetime import datetime
from sqlalchemy import select, and_

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student, User, TutorGroup, Staff
from config import BOT_TOKEN, OWNER_TELEGRAM_ID
from aiogram import Bot
from aiogram.types import FSInputFile

async def main():
    print("Generating missing users report...")
    async with AsyncSessionLocal() as session:
        # Query: Active Students who are NOT in User table
        query = (
            select(
                Student.full_name,
                Student.faculty_name,
                Student.specialty_name,
                Student.group_number,
                Staff.full_name.label("tutor_name"),
                Student.phone,
                Student.hemis_id
            )
            .outerjoin(User, Student.hemis_login == User.hemis_login)
            .outerjoin(TutorGroup, Student.group_number == TutorGroup.group_number)
            .outerjoin(Staff, TutorGroup.tutor_id == Staff.id)
            .where(User.id == None) # Not in User table
            # .where(Student.status == 'active') # Optional: only active students
            .order_by(Student.faculty_name, Student.group_number, Student.full_name)
        )
        
        result = await session.execute(query)
        rows = result.all()
        
        # Prepare CSV
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/kirmagan_talabalar_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        count = 0
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(["Fakultet", "Yo'nalish", "Guruh", "Tyutor", "F.I.SH", "Telefon", "HEMIS ID"])
            
            for r in rows:
                writer.writerow([
                    r.faculty_name or "Noma'lum",
                    r.specialty_name or "Noma'lum",
                    r.group_number or "Guruhsiz",
                    r.tutor_name or "Biriktirilmagan",
                    r.full_name,
                    r.phone or "",
                    r.hemis_id or ""
                ])
                count += 1
                
        print(f"Report generated: {filename}")
        print(f"Total missing users: {count}")
        
        # Send via Telegram
        if BOT_TOKEN and OWNER_TELEGRAM_ID:
            try:
                bot = Bot(token=BOT_TOKEN)
                await bot.send_document(
                    chat_id=OWNER_TELEGRAM_ID,
                    document=FSInputFile(filename),
                    caption=f"📉 **Platformaga kirmagan talabalar**\n\nJami: {count} nafar\nFormat: CSV"
                )
                print("Sent to Telegram.")
                await bot.session.close()
            except Exception as e:
                print(f"Failed to send telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())

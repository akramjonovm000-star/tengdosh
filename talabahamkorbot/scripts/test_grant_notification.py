import asyncio
import logging
import sys
import os

# Add parent dir to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student
from services.hemis_service import HemisService
from services.gpa_calculator import GPACalculator
from config import BOT_TOKEN
from aiogram import Bot

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_TG_ID = 7476703866

async def run_test():
    print(f"--- Grant Notification Test (Real User) ---")
    print(f"Target TG ID: {TARGET_TG_ID}")

    async with AsyncSessionLocal() as session:
        # 1. Find Student by Telegram ID
        stmt = select(TgAccount).options(selectinload(TgAccount.student)).where(TgAccount.telegram_id == TARGET_TG_ID)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account or not account.student:
            print("❌ Student not found for this Telegram ID.")
            return

        student = account.student
        print(f"✅ Found Student: {student.full_name} ({student.hemis_login})")
        
        # 2. Authenticate / Refresh Token
        token = student.hemis_token
        # Verify token works or re-login
        me = await HemisService.get_me(token)
        if not me and student.hemis_login and student.hemis_password:
             print("Refreshing token...")
             token, _ = await HemisService.authenticate(student.hemis_login, student.hemis_password)
        
        if not token:
             print("❌ Could not get valid token.")
             return

    # 3. Get Subjects (Semester 11)
    current_sem = "11" 
    print(f"Checking Semester: {current_sem}")

    subjects = await HemisService.get_student_subject_list(token, semester_code=current_sem)
    if not subjects:
        print("❌ No subjects found.")
        return

    print(f"Found {len(subjects)} subjects.")
    
    # DEBUG: Print details
    for s in subjects:
        name = s.get("subject", {}).get("name") or s.get("curriculumSubject", {}).get("subject", {}).get("name")
        credit = s.get("credit") or s.get("curriculumSubject", {}).get("credit")
        grade = s.get("overallScore", {}).get("grade")
        print(f" - {name} | Credit: {credit} | Grade: {grade}")

    # 4. Calculate GPA (5-point scale)
    gpa_result = GPACalculator.calculate_gpa(subjects)
    gpa = gpa_result.gpa
    
    # 5. Calculate Grant Score
    grant_score = round(gpa * 16, 2)

    print(f"\n📊 RESULTS:")
    print(f"GPA (5-scale): {gpa}")
    print(f"Grant Score (GPA * 16): {grant_score}")

    # 6. Draft Message
    if grant_score >= 80:
        score_msg_part = f"⚖️ Yozgi grant qayta taqsimlashda akademik o'zlashtirishdan: <b>Maksimal {grant_score} ball</b> oldingiz! 🔥"
    else:
        score_msg_part = f"⚖️ Yozgi grant qayta taqsimlashda akademik o'zlashtirishdan: <b>{grant_score} ball</b> olarkansiz."

    msg = (
        f"👋 Assalomu alaykum!\n\n"
        f"🎉 <b>Tabriklaymiz!</b> Siz barcha yakuniy nazoratlardan baho oldingiz.\n\n"
        f"📊 Sizning joriy GPA ko'rsatkichingiz: <b>{gpa}</b>\n"
        f"{score_msg_part}\n\n"
        f"🏆 Grant uchun kurashda g'alaba qozonish uchun <b>ijtimoiy faollikni</b> ham unutmang!"
    )

    print("\n📩 Sending Message...")
    
    # 7. Send via Bot
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=TARGET_TG_ID, text=msg, parse_mode="HTML")
        await bot.session.close()
        print("✅ Message Sent Successfully!")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())

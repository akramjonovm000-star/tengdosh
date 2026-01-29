import asyncio
import logging
import sys
import os

# Add parent dir to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, desc
from database.db_connect import AsyncSessionLocal
from database.models import Student
from services.hemis_service import HemisService
from services.gpa_calculator import GPACalculator
from config import BOT_TOKEN
from aiogram import Bot

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_LOGIN = "395251101411"
TEST_PASSWORD = "6161234a"
TEST_TG_ID = 8155790902

async def run_test():
    print(f"--- Grant Notification with Leaderboard Test ---")
    
    # 1. Authenticate Test User & Calc Score
    print(f"Calculating Score for {TEST_LOGIN}...")
    token, _ = await HemisService.authenticate(TEST_LOGIN, TEST_PASSWORD)
    if not token:
        print("Auth failed")
        return

    # Get Subjects (Sem 11)
    subjects = await HemisService.get_student_subject_list(token, semester_code="11")
    if not subjects:
        print("No subjects found (Sem 11)")
        return
        
    gpa_result = GPACalculator.calculate_gpa(subjects)
    my_gpa = gpa_result.gpa
    my_score = round(my_gpa * 16, 2)
    
    print(f"My GPA: {my_gpa} | Score: {my_score}")
    
    # 2. Build Leaderboard from DB
    # We assume other students' GPA is in the DB (student.gpa).
    # Since we haven't synced everyone with the new logic, many might be 0.
    # But we will use what we have.
    
    async with AsyncSessionLocal() as session:
        # Fetch all active students with valid GPA
        stmt = select(Student).where(Student.is_active == True).order_by(desc(Student.gpa))
        result = await session.execute(stmt)
        all_students = result.scalars().all()
        
        # Prepare list for sorting
        # We need to include "CURRENT" calculated user in this list if they aren't updated in DB yet.
        # Or just update the DB object for the test user temporarily?
        # Let's verify if the test user is in the list.
        
        leaderboard_data = []
        found_me = False
        
        for s in all_students:
            # If this is me, use the FRESH calculation
            if s.hemis_login == TEST_LOGIN:
                s_gpa = my_gpa
                found_me = True
                my_name = s.full_name
            else:
                s_gpa = s.gpa or 0.0
            
            s_score = round(s_gpa * 16, 2)
            leaderboard_data.append({
                "name": s.full_name,
                "score": s_score,
                "is_me": (s.hemis_login == TEST_LOGIN)
            })
            
        if not found_me:
             # Add me if not in DB?
             leaderboard_data.append({
                "name": "Test User",
                "score": my_score,
                "is_me": True
            })
            
        # Sort by Score DESC
        leaderboard_data.sort(key=lambda x: x["score"], reverse=True)
        
        # Find Rank
        my_rank = -1
        for idx, item in enumerate(leaderboard_data):
            if item["is_me"]:
                my_rank = idx + 1
                break
                
        # Top 10
        top_10 = leaderboard_data[:10]
        
    # 3. Build Message
    if my_score >= 80:
        score_msg_part = f"⚖️ Yozgi grant qayta taqsimlashda akademik o'zlashtirishdan: <b>Maksimal {my_score} ball</b> oldingiz! 🔥"
    else:
        score_msg_part = f"⚖️ Yozgi grant qayta taqsimlashda akademik o'zlashtirishdan: <b>{my_score} ball</b> olarkansiz."

    leaderboard_text = "\n🏆 <b>TOP 10 LIDERLAR:</b>\n"
    for i, s in enumerate(top_10, 1):
        name_short = s["name"]
        # Abbreviate name? "Rahimxonov Javohirxon" -> "Rahimxonov J."
        parts = name_short.split()
        if len(parts) >= 2:
            name_short = f"{parts[0]} {parts[1][0]}."
            
        mark = "🔹" if not s['is_me'] else "🟢"
        bold_start = "<b>" if s['is_me'] else ""
        bold_end = "</b>" if s['is_me'] else ""
        
        leaderboard_text += f"{i}. {mark} {bold_start}{name_short}: {s['score']}{bold_end}\n"

    msg = (
        f"👋 Assalomu alaykum!\n\n"
        f"🎉 <b>Tabriklaymiz!</b> Siz barcha yakuniy nazoratlardan baho oldingiz.\n\n"
        f"📊 Sizning joriy GPA ko'rsatkichingiz: <b>{my_gpa}</b>\n"
        f"{score_msg_part}\n\n"
        f"📈 <b>Reyting:</b> Siz {len(leaderboard_data)} ta talaba orasida <b>{my_rank}-o'rinda</b> turibsiz.\n"
        f"{leaderboard_text}\n"
        f"🏆 Grantda g'alaba qozonish uchun <b>ijtimoiy faollikni</b> (20 ball) maksimal qilishni unutmang!"
    )
    
    print("\n📩 Sending Message...")
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=TEST_TG_ID, text=msg, parse_mode="HTML")
        await bot.session.close()
        print("✅ Message Sent!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())

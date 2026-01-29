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

TARGET_TG_ID = 8155790902
SEMESTER_CODE = "11"

async def test_leaderboard_names():
    print(f"--- LEADERBOARD NAME FIX TEST ---")
    print(f"Target Admin ID: {TARGET_TG_ID}")
    
    bot = Bot(token=BOT_TOKEN)
    student_scores = []
    
    try:
        async with AsyncSessionLocal() as session:
            # 1. Fetch ALL Students with Telegram
            stmt = select(TgAccount).options(selectinload(TgAccount.student))
            result = await session.execute(stmt)
            accounts = result.scalars().all()
            
            print(f"Found {len(accounts)} students to check.")
            
            for i, acc in enumerate(accounts):
                student = acc.student
                if not student: continue
                
                # Authenticate & Refresh Name
                token = student.hemis_token
                
                try:
                    # Always try to fetch updated profile to fix "Talaba"
                    if "Talaba" in student.full_name or "Student" in student.full_name or not student.full_name:
                        if student.hemis_login and student.hemis_password:
                            me_data = await HemisService.get_me(token)
                            if not me_data:
                                 token, _ = await HemisService.authenticate(student.hemis_login, student.hemis_password)
                                 student.hemis_token = token
                                 me_data = await HemisService.get_me(token)
                            
                            if me_data:
                                lname = me_data.get("surname") or ""
                                fname = me_data.get("firstname") or ""
                                full_name = f"{lname} {fname}".strip()
                                if full_name:
                                    student.full_name = full_name
                                    session.add(student)
                                    print(f"  ✅ Updated Name (HEMIS): {full_name}")
                except Exception as e:
                    print(f"  ⚠️ Name refresh error: {e}")

                # Fallback to Telegram Name (via Bot API)
                if (not student.full_name or "Talaba" in student.full_name or "User" in student.full_name):
                     try:
                         chat = await bot.get_chat(acc.telegram_id)
                         tg_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip()
                         if tg_name:
                             student.full_name = f"{tg_name} (TG)"
                             session.add(student)
                             print(f"  ⚠️ Used Telegram Name: {student.full_name}")
                             # Rate limit for Telegram API
                             await asyncio.sleep(0.2)
                     except Exception as e:
                         print(f"  ❌ Telegram fetch failed for {acc.telegram_id}: {e}")
                
                # FORCE RECALCULATE GPA to verify new logic (exclude_in_progress=False)
                try:
                    subjects = await HemisService.get_student_subject_list(token, semester_code=SEMESTER_CODE)
                    if subjects:
                         gpa_res = GPACalculator.calculate_gpa(subjects, exclude_in_progress=False)
                         gpa = gpa_res.gpa
                         
                         # Save to DB for consistency
                         student.gpa = gpa
                         session.add(student)
                    else:
                         gpa = 0.0
                except Exception as e:
                    print(f"  ❌ Calc error {acc.telegram_id}: {e}")
                    gpa = student.gpa or 0.0 # Fallback

                score = round(gpa * 16, 2)
                
                # Strict Filter: GPA >= 3.0
                if gpa >= 3.0:
                    student_scores.append({
                        "name": student.full_name,
                        "score": score,
                        "tg_id": acc.telegram_id
                    })
                else:
                    print(f"  Skipping {student.full_name} (GPA {gpa})")
            
            await session.commit()
            
        print(f"\nQualified for Leaderboard: {len(student_scores)}")
        
        # Sort
        student_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Build FULL List (Up to 100)
        top_list = student_scores[:100]
        
        leaderboard_text = f"\n🏆 <b>LIDERLAR ({len(student_scores)} ta):</b>\n"
        for i, leader in enumerate(top_list, 1):
            name = leader["name"]
            score = leader["score"]
            if score >= 80: score = "80.0" 

            leaderboard_text += f"{i}. 🔹 {name}: {score}\n"
            
        # Split message if too long
        if len(leaderboard_text) > 3000:
            leaderboard_text = leaderboard_text[:3000] + "\n... (davomi bor)"
            
        msg = (
            f"👋 <b>TEST XABAR (Faqat sizga)</b>\n\n"
            f"Mana yangilangan To'liq Leaderboard (Ismlar bilan):\n"
            f"{leaderboard_text}\n"
            f"Agar ismlar to'g'ri bo'lsa, tasdiqlang."
        )
        
        print("\n📩 Sending to Admin...")
        try:
            await bot.send_message(chat_id=TARGET_TG_ID, text=msg, parse_mode="HTML")
            print("✅ Sent!")
        except Exception as e:
            print(f"❌ Failed: {e}")
            
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_leaderboard_names())

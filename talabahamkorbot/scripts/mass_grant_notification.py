import asyncio
import logging
import sys
import os
import time

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

# SEMESTER TO CHECK
SEMESTER_CODE = "11"

async def mass_notify():
    print(f"--- MASS GRANT NOTIFICATION (Semester {SEMESTER_CODE}) ---")
    
    # List to store processed data for Leaderboard
    student_scores = []
    
    async with AsyncSessionLocal() as session:
        # 1. Fetch ALL Students with Telegram
        stmt = select(TgAccount).options(selectinload(TgAccount.student))
        result = await session.execute(stmt)
        accounts = result.scalars().all()
        
        print(f"Found {len(accounts)} students with Telegram.")
        
        # 2. Sync Data & Calculate Scores
        print("\n--- Phase 1: Calculating Scores ---")
        for i, acc in enumerate(accounts):
            student = acc.student
            if not student: continue
            
            print(f"[{i+1}/{len(accounts)}] Processing {student.full_name}...")
            
            # Authenticate
            token = student.hemis_token
            
            # Check/Refresh Name if it looks generic
            if student.full_name in ["Talaba", "Student", "None", None] or "Talaba" in student.full_name:
                print("  Refreshing Profile Name...")
                try:
                    me_data = await HemisService.get_me(token)
                    if not me_data and student.hemis_login and student.hemis_password:
                         token, _ = await HemisService.authenticate(student.hemis_login, student.hemis_password)
                         student.hemis_token = token
                         me_data = await HemisService.get_me(token)
                    
                    if me_data:
                        # Update Name
                        lname = me_data.get("surname") or ""
                        fname = me_data.get("firstname") or ""
                        pname = me_data.get("patronymic") or ""
                        full_name = f"{lname} {fname} {pname}".strip()
                        if full_name:
                            student.full_name = full_name
                            print(f"  Authored Name: {full_name}")
                except Exception as e:
                    print(f"  Name refresh failed: {e}")

            # Simple check if token works or refresh
            # We skip full `get_me` check to save time, assume token might work or try quick fetch
            try:
                subjects = await HemisService.get_student_subject_list(token, semester_code=SEMESTER_CODE)
                
                # If invalid token, try login
                if subjects is None: # None indicates Auth error usually in my service logic
                    if student.hemis_login and student.hemis_password:
                        print("  Refreshing token...")
                        token, _ = await HemisService.authenticate(student.hemis_login, student.hemis_password)
                        student.hemis_token = token
                        # Retry fetch
                        subjects = await HemisService.get_student_subject_list(token, semester_code=SEMESTER_CODE)
            except Exception as e:
                print(f"  Error fetching: {e}")
                subjects = []

            if not subjects:
                print("  No subjects or access denied. Skipping.")
                continue

            # Calculate
            # exclude_in_progress=False so that 0 grades count as failures (lowering GPA) 
            # instead of being ignored (which inflates GPA if they have 1 good grade)
            gpa_res = GPACalculator.calculate_gpa(subjects, exclude_in_progress=False)
            gpa = gpa_res.gpa
            score = round(gpa * 16, 2)
            
            # Filter: Only those who have VALID grades (GPA >= 3.0)
            # This excludes students like Shahribonu (2.4 due to failures)
            if gpa >= 3.0:
                print(f"  GPA: {gpa} | Score: {score}")
                
                # Update DB
                student.gpa = gpa
                session.add(student)
                
                student_scores.append({
                    "name": student.full_name,
                    "score": score,
                    "gpa": gpa,
                    "tg_id": acc.telegram_id,
                    "student_id": student.id
                })
            else:
                print(f"  GPA too low ({gpa}). Skipping.")
            
            # Rate limit protection for HEMIS
            await asyncio.sleep(0.5)
            
        await session.commit()
        
    print(f"\n--- Phase 2: Building Leaderboard ---")
    # Sort by Score DESC
    student_scores.sort(key=lambda x: x["score"], reverse=True)
    
    total_students = len(student_scores)
    print(f"Total Qualified Students: {total_students}")
    
    # Top 10 Text
    top_10 = student_scores[:10]
    
    print("\n--- Phase 3: Sending Messages ---")
    bot = Bot(token=BOT_TOKEN)
    
    try:
        sent_count = 0
        for rank_idx, s_data in enumerate(student_scores):
            rank = rank_idx + 1
            
            # Build Leaderboard Text (Personalized highlight)
            leaderboard_text = "\n🏆 <b>TOP 10 LIDERLAR:</b>\n"
            for i, leader in enumerate(top_10, 1):
                name_parts = leader["name"].split()
                short_name = f"{name_parts[0]} {name_parts[1][0]}." if len(name_parts) >= 2 else leader["name"]
                
                is_me = (leader["student_id"] == s_data["student_id"])
                mark = "🟢" if is_me else "🔹"
                b_start = "<b>" if is_me else ""
                b_end = "</b>" if is_me else ""
                
                leaderboard_text += f"{i}. {mark} {b_start}{short_name}: {leader['score']}{b_end}\n"

            # Custom Message
            if s_data["score"] >= 80:
                 score_txt = f"Maksimal {s_data['score']} ball"
            else:
                 score_txt = f"{s_data['score']} ball"

            msg = (
                f"👋 Assalomu alaykum!\n\n"
                f"🎉 <b>Tabriklaymiz!</b> Siz barcha yakuniy nazoratlardan baho oldingiz.\n\n"
                f"📊 Sizning joriy GPA ko'rsatkichingiz: <b>{s_data['gpa']}</b>\n"
                f"⚖️ Yozgi grant qayta taqsimlashda akademik o'zlashtirishdan: <b>{score_txt}</b> oldingiz! 🔥\n\n"
                f"📈 <b>Reyting:</b> Siz {total_students} ta talaba orasida <b>{rank}-o'rinda</b> turibsiz.\n"
                f"{leaderboard_text}\n"
                f"🏆 Grantda g'alaba qozonish uchun <b>ijtimoiy faollikni</b> (20 ball) maksimal qilishni unutmang!"
            )
            
            try:
                await bot.send_message(chat_id=s_data["tg_id"], text=msg, parse_mode="HTML")
                print(f"✅ Sent to {s_data['name']} ({rank})")
                sent_count += 1
            except Exception as e:
                print(f"❌ Failed to {s_data['name']}: {e}")
            
            # Telegram Rate Limit (30 msg/sec limit, but be safe with 0.1s)
            await asyncio.sleep(0.1)
            
    finally:
        await bot.session.close()
        
    print(f"\n✅ DONE. Sent {sent_count} messages.")

if __name__ == "__main__":
    asyncio.run(mass_notify())

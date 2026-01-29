import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount
from services.hemis_service import HemisService
from bot import bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def broadcast_grades():
    logger.info("📢 Starting Grade Broadcast...")
    
    async with AsyncSessionLocal() as session:
        # Get students with Telegram accounts
        stmt = select(Student).where(Student.is_active == True, Student.hemis_token.is_not(None)).options(selectinload(Student.tg_accounts))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        sent_count = 0
        
        for student in students:
            if not student.tg_accounts:
                continue
                
            tg_id = student.tg_accounts[0].telegram_id
            
            try:
                # Fetch fresh subjects
                subjects = await HemisService.get_student_subject_list(student.hemis_token)
                if not subjects:
                    logger.warning(f"No subjects found for {student.full_name}")
                    continue
                
                # Check for YN grades
                yn_list = []
                for subj in subjects:
                    parsed = HemisService.parse_grades_detailed(subj)
                    yn_score = parsed["YN"]["raw"]
                    if yn_score > 0:
                        curr_subj = subj.get("curriculumSubject", {})
                        subj_data = curr_subj.get("subject", {}) or subj.get("subject", {})
                        subj_name = subj_data.get("name") or "Noma'lum fan"
                        
                        yn_list.append(f"✅ <b>{subj_name}</b>: {yn_score} ball")
                
                # Construct Message
                header = "📢 <b>YAKUNIY NAZORAT (YN) HISOBOTI</b>\n\n"
                
                if yn_list:
                    body = "Hozirgacha quyidagi fanlardan Yakuniy baholar qo'yilgan:\n\n" + "\n".join(yn_list)
                else:
                    body = "Hozirgacha hech qaysi fandan Yakuniy baho (YN) qo'yilmagan."
                
                footer = (
                    "\n\n────────────────\n"
                    "🚀 <b>YANGILIK:</b>\n"
                    "Bot endi baholaringizni doimiy kuzatib boradi.\n"
                    "Yangi baho chiqishi bilan sizga darhol xabar beramiz!\n\n"
                    "<i>Siz faqat kuting, bot o'zi xabar beradi!</i> 😎"
                )
                
                full_msg = header + body + footer
                
                await bot.send_message(tg_id, full_msg, parse_mode="HTML")
                logger.info(f"Sent to {student.full_name} ({tg_id})")
                sent_count += 1
                
                # Sleep briefly to be nice to Telegram API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to send to {student.full_name}: {e}")

    logger.info(f"✅ Broadcast finished. Sent to {sent_count} users.")

if __name__ == "__main__":
    asyncio.run(broadcast_grades())

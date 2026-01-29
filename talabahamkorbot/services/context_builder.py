
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Student, UserActivity
# from services.hemis_service import get_student_schedule
# from services.hemis_service import get_grades # Need to implement or check existance

import asyncio
from celery_app import app as celery_app
from database.db_connect import AsyncSessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(name="daily_context_update")
def run_daily_context_update():
    """Celery task wrapper for global context update"""
    return asyncio.run(bulk_update_contexts())

async def bulk_update_contexts():
    """Tashkent vaqti bilan 03:00-04:00 orasi (UTC 22:00-23:00)"""
    logger.info("🕛 Starting Global Daily AI Context Update...")
    async with AsyncSessionLocal() as session:
        # Get active students
        stmt = select(Student).where(Student.is_active == True)
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        count = 0
        for student in students:
            try:
                await build_student_context(session, student.id)
                count += 1
            except Exception as e:
                logger.error(f"Context update failed for student {student.id}: {e}")
        
        await session.commit()
    logger.info(f"✅ Daily Context Update Finished. Updated {count} students.")

async def build_student_context(session: AsyncSession, student_id: int) -> str:
    """
    Talaba haqida barcha ma'lumotlarni yig'ib, AI uchun matn shaklida qaytaradi.
    Shu bilan birga bazaga (ai_context) saqlaydi.
    """
    stmt = select(Student).where(Student.id == student_id)
    result = await session.execute(stmt)
    student = result.scalar_one_or_none()

    if not student:
        return ""

    
    # 0. Avto-Login va Token Tekshiruvi
    from services.hemis_service import HemisService
    from aiogram import Bot
    from config import BOT_TOKEN
    import os
    
    # Initialize bot for notifications (hacky but works for service layer)
    # Better to pass bot instance, but for now strict implementation
    bot = Bot(token=BOT_TOKEN)

    try:
        # Check if token is valid by fetching ME
        me_data = None
        if student.hemis_token:
            me_data = await HemisService.get_me(student.hemis_token)
        
        # If invalid/expired (None) AND we have password -> Refresh
        if not me_data and student.hemis_login and student.hemis_password:
            logger.info(f"Context Update: Token expired for {student.id}, refreshing...")
            new_token, err = await HemisService.authenticate(student.hemis_login, student.hemis_password)
            
            if new_token:
                student.hemis_token = new_token
                me_data = await HemisService.get_me(new_token)
            else:
                # Login failed. Check precise reason.
                logger.warning(f"Context Update: Auto-login failed for {student.id}. Reason: {err}")
                
                # ONLY Notify if it is strictly an Authentication Failure (Wrong Password)
                # Ignore "SERVER_ERROR" or "NO_TOKEN" (Transient issues)
                if err == "AUTH_FAILED" and student.tg_accounts:
                    tg_id = student.tg_accounts[0].telegram_id
                    try:
                        await bot.send_message(
                            tg_id,
                            "⚠️ <b>Diqqat!</b>\n\n"
                            "Universitet tizimidagi <b>parolingiz o'zgarganga o'xshaydi</b> (yoki noto'g'ri).\n"
                            "Bot ma'lumotlaringizni yangilay olmadi. Iltimos, qayta kirish (Login) qiling.",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                         # Blocked user etc.
                        logger.error(f"Failed to notify user {tg_id}: {e}")
                
                elif err == "SERVER_ERROR":
                     # Silent log, do not bother user. They can't fix server issues.
                     logger.info(f"Skipping notification for {student.id} due to Server Error.")

        # Update Name from latest data
        if me_data:
             f_name_parts = [
                 me_data.get('firstname', ''), 
                 me_data.get('lastname', ''), 
                 me_data.get('fathername', '')
             ]
             f_name = " ".join(filter(None, f_name_parts)).strip()
             if f_name:
                 student.full_name = f_name

    except Exception as e:
        logger.error(f"Error in Context Auto-Login: {e}")
    finally:
        await bot.session.close() # Important to close bot session

    # 1. Shaxsiy Ma'lumotlar
    context_lines = [
        f"TALABA MA'LUMOTLARI:",
        f"Ism: {student.full_name}",
        f"Universitet: {student.university_name or 'Namalum'}",
        f"Fakultet: {student.faculty_name or 'Namalum'}",
        f"Yo'nalish: {student.specialty_name or 'Namalum'}",
        f"Bosqich: {student.level_name or 'Namalum'}, {student.semester_name or 'Namalum'}",
        f"Guruh: {student.group_number or 'Namalum'}",
        f"Ta'lim turi: {student.education_type}, {student.education_form}",
        f"To'lov shakli: {student.payment_form}",
        f"Qoldirilgan soatlar: {student.missed_hours}",
    ]

    # 2. O'zlashtirish (Baholar) - CURRENT SEMESTER & GPA
    # Try fetching via API first
    grades_text = "Ma'lumot yo'q"
    try:
        if student.hemis_token:
            # A. API Method
            grades_data = await HemisService.get_student_performance_details(student.hemis_token)
            
            # B. Fallback to Scrape if API empty but we have credentials
            if not grades_data and student.hemis_login and student.hemis_password:
                 logger.info(f"Context: API grades empty for {student.id}, scraping...")
                 grades_data, _ = await HemisService.scrape_grades_with_credentials(student.hemis_login, student.hemis_password)
            
            if grades_data:
                g_lines = []
                for g in grades_data:
                    sub_name = "Fan"
                    score = "0"
                    
                    if isinstance(g.get("subject"), dict):
                        sub_name = g.get("subject", {}).get("name", "Fan")
                    
                    # Check for 5-grade system flag or explicit grade key
                    if g.get("is_5_grade"):
                        val = g.get("total_score", 0)
                        score = f"{val} baho"
                    elif "total_score" in g:
                        score = f"{g['total_score']} ball"
                    elif "grade" in g:
                         score = f"{g['grade']} baho"
                    
                    g_lines.append(f"- {sub_name}: {score}")
                
                if g_lines:
                    grades_text = "\n".join(g_lines)
    except Exception as e:
        logger.error(f"Context Grade Fetch Error: {e}")

    context_lines.append(f"\nBAHOLAR (Joriy):\n{grades_text}")

    # 3. Dars Jadvali (Bugun va Ertaga)
    # Jadvalni olish uchun login/parol kerak emas, jmcu api ochiq
    # Lekin bizda student uchun token kerak bo'lishi mumkin.
    # Hozircha statik yoki oxirgi saqlangan ma'lumotni olishga harakat qilamiz.
    # Agar jadval servisi bo'lsa:
    # try:
    #     schedule = await get_schedule(student.hemis_token)
    #     context_lines.append(f"\nDARS JADVALI: {schedule}")
    # except:
    #     pass

    # 3. Faolliklar
    stmt_act = select(UserActivity).where(UserActivity.student_id == student_id)
    res_act = await session.execute(stmt_act)
    activities = res_act.scalars().all()
    
    if activities:
        context_lines.append("\nFAOLLIKLARI:")
        for act in activities:
            context_lines.append(f"- {act.name} ({act.category}): {act.status}")

    # 4. Yakuniy matn
    full_text = "\n".join(context_lines)
    
    # Bazaga saqlash
    student.ai_context = full_text
    student.last_context_update = datetime.utcnow()
    # session.add(student) # Caller commits
    
    return full_text

import logging
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount, StudentNotification
from services.hemis_service import HemisService
from services.notification_service import NotificationService

from celery_app import app as celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="sync_all_students")
def run_sync_all_students():
    """Celery task wrapper for global sync"""
    return asyncio.run(sync_all_students())

async def sync_all_students():
    """
    Kunda 1 marta barcha aktiv talabalarni HEMIS bilan sinxronizatsiya qiladi.
    """
    logger.info("Starting Global HEMIS Sync...")
    async with AsyncSessionLocal() as session:
        stmt = select(Student).where(Student.is_active == True)
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        count = 0
        for student in students:
            try:
                await sync_student_data(session, student.id)
                count += 1
                # Prevent Rate Limiting
                await asyncio.sleep(0.5) 
            except Exception as e:
                logger.error(f"Sync failed for student {student.id}: {e}")
        
        await session.commit()
    logger.info(f"Global Sync Finished. Updated {count} students.")

async def sync_student_data(session: AsyncSession, student_id: int):
    """
    Bitta talaba uchun barcha muhim ma'lumotlarni yangilaydi.
    """
    stmt = select(Student).where(Student.id == student_id)
    result = await session.execute(stmt)
    student = result.scalar_one_or_none()
    if not student: return

    # 1. Refresh Token if needed & Get Profile
    me_data = None
    if student.hemis_token:
        me_data = await HemisService.get_me(student.hemis_token)
    
    # Auto-refresh logic
    if not me_data and student.hemis_login and student.hemis_password:
        token, err = await HemisService.authenticate(student.hemis_login, student.hemis_password)
        if token:
            student.hemis_token = token
            me_data = await HemisService.get_me(token)
    
    if not me_data:
        logger.warning(f"Sync: Could not get profile for student {student_id}")
        return

    # 2. Update Profile Fields
    # Fetch Semesters to find latest active
    semesters = await HemisService.get_semester_list(student.hemis_token)
    
    current_sem = None
    if semesters:
        # ALWAYS pick the latest semester available (highest ID)
        # This overrides 'current' flag which is often outdated in university systems
        current_sem = semesters[0]

    if current_sem:
        student.semester_name = current_sem.get("name")
    
    level = me_data.get("level", {})
    if level:
        student.level_name = level.get("name")

    group = me_data.get("group", {})
    if group:
        student.group_number = group.get("name")

    # 3. Update Attendance (Missed Hours)
    # Get current semester code for accurate data
    sem_code = None
    if current_sem:
        sem_code = str(current_sem.get("code") or current_sem.get("id") or "")
        
    total, excused, unexcused, attendance_list = await HemisService.get_student_absence(
        student.hemis_token, 
        semester_code=sem_code
    )
    
    old_missed = student.missed_hours or 0
    
    # Recalculate precisely
    cur_total, cur_excused, cur_unexcused = 0, 0, 0
    for item in attendance_list:
        h = item.get("hour") or 2
        status = item.get("absent_status", {}).get("code")
        if status == "11" or item.get("is_valid") == True:
            cur_excused += h
        else:
            cur_unexcused += h
        cur_total += h

    student.missed_hours = cur_total
    student.missed_hours_excused = cur_excused
    student.missed_hours_unexcused = cur_unexcused
    
    if cur_total > old_missed:
        await _notify_attendance(student, cur_total, old_missed)

    # 4. Update Performance (GPA) - Match Bot Logic
    # The Bot gets 5.0 by passing None (fetching 'default' active subjects - often more reliable)
    gpa = await HemisService.get_student_performance(student.hemis_token, semester_code=None)
    
    # [FALLBACK] If default returns 0 (likely new semester started), try explicit semesters
    if gpa == 0.0 and semesters:
        # Try current explicit code (e.g. 12)
        gpa = await HemisService.get_student_performance(student.hemis_token, semester_code=sem_code)
        
        # If still 0, try the PREVIOUS semester (e.g. 11)
        if gpa == 0.0 and len(semesters) > 1:
            prev_sem = semesters[1]
            prev_code = str(prev_sem.get("code") or prev_sem.get("id") or "")
            logger.info(f"Sync: Fallback to previous semester: {prev_code}")
            prev_gpa = await HemisService.get_student_performance(student.hemis_token, semester_code=prev_code)
            if prev_gpa > 0:
                gpa = prev_gpa

    student.gpa = gpa
    
    # Update updated_at
    student.updated_at = datetime.utcnow()
    
    logger.info(f"Sync: Updated data for {student.full_name}")

async def _notify_attendance(student: Student, new_total: int, old_total: int):
    """Notify user about attendance jump"""
    from bot import bot
    # Fetch Telegram ID
    async with AsyncSessionLocal() as session:
        stmt = select(TgAccount).where(TgAccount.student_id == student.id)
        res = await session.execute(stmt)
        acc = res.scalar_one_or_none()
        
        if acc:
            diff = new_total - old_total
            msg = (
                "📉 <b>Davomat yangilandi</b>\n\n"
                f"Sizda <b>+{diff}</b> soat yangi qoldirilgan dars aniqlandi.\n"
                f"Jami qoldirilgan: <b>{new_total}</b> soat.\n\n"
                "⚠️ O'z vaqtida sababli hujjatlarni taqdim etishni unutmang!"
            )
            try:
                await bot.send_message(acc.telegram_id, msg, parse_mode="HTML")
            except: pass
        
        # [NEW] Push Notification
        if student.fcm_token:
            title = "📉 Davomat yangilandi"
            body = f"Sizda +{new_total - old_total} soat yangi qoldirilgan dars aniqlandi."
            await NotificationService.send_push(
                token=student.fcm_token,
                title=title,
                body=body,
                data={"type": "attendance"}
            )

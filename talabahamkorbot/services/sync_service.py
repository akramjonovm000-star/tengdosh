import logging
import asyncio
import re
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
    semesters = await HemisService.get_semester_list(student.hemis_token, student_id=student.id)
    
    current_sem = None
    if semesters:
        # 1. Try finding explicitly marked 'current' semester
        for sem in semesters:
             if sem.get("current") is True:
                 current_sem = sem
                 break
        
        # 2. If no current flag, fallback to latest ID
        if not current_sem:
             current_sem = semesters[0]

    if current_sem:
        student.semester_name = current_sem.get("name")
    
    level = me_data.get("level", {})
    if level:
        student.level_name = level.get("name")

    group = me_data.get("group", {})
    if group:
        student.group_number = group.get("name")

    # Update Full Name (Robust extraction)
    first_name = me_data.get("first_name") or me_data.get("firstname") or me_data.get("firstName") or ""
    last_name = me_data.get("second_name") or me_data.get("lastname") or me_data.get("surname") or me_data.get("lastName") or ""
    patronymic = me_data.get("third_name") or me_data.get("fathername") or me_data.get("patronymic") or me_data.get("secondName") or ""
    
    full_name_constructed = f"{last_name} {first_name} {patronymic}".strip()
    full_name_hemis = (me_data.get("full_name") or me_data.get("fullName") or "").strip().title()

    def count_initials(name):
        return len(re.findall(r'\b[A-Z]\.', name))

    if full_name_hemis and count_initials(full_name_hemis) <= count_initials(full_name_constructed):
        best_full_name = full_name_hemis
    else:
        best_full_name = full_name_constructed

    if best_full_name and student.full_name != best_full_name:
        student.full_name = best_full_name

    # 3. Update Attendance (Missed Hours)
    # Get current semester code for accurate data
    sem_code = None
    if current_sem:
        sem_code = str(current_sem.get("code") or current_sem.get("id") or "")
        
    old_missed = student.missed_hours or 0
    
    # [ACCURACY] Try explicit latest semester ONLY (for 'Current' view)
    total, excused, unexcused, attendance_list = 0, 0, 0, []
    if sem_code:
        total, excused, unexcused, attendance_list = await HemisService.get_student_absence(
            student.hemis_token, 
            semester_code=sem_code,
            student_id=student.id,
            force_refresh=False # Respect cache logic
        )
    else:
        # If no semester found yet, try default (often current)
        total, excused, unexcused, attendance_list = await HemisService.get_student_absence(
            student.hemis_token, 
            semester_code=None,
            student_id=student.id,
            force_refresh=False
        )

    # Safety: Ensure total is the sum if there's any discrepancy
    # HEMIS sometimes returns inconsistent total field
    if total < (excused + unexcused):
        total = excused + unexcused

    student.missed_hours = total
    student.missed_hours_excused = excused
    student.missed_hours_unexcused = unexcused
    
    if total > old_missed:
        await _notify_attendance(student, total, old_missed)

    # 4. Update Performance (GPA) - Prioritize current semester
    gpa = 0.0
    if sem_code:
        gpa = await HemisService.get_student_performance(student.hemis_token, student_id=student.id, semester_code=sem_code)
    
    # Fallback to default if 0
    if gpa == 0.0:
        gpa = await HemisService.get_student_performance(student.hemis_token, student_id=student.id, semester_code=None)
        
    # [DEEP FALLBACK] If still 0, try finding ANY recent semester with GPA > 0
    if gpa == 0.0 and semesters:
        # Sorted semesters loop
        for i in range(1, min(len(semesters), 5)): # Check last 5 semesters max to avoid overhead
            prev_sem = semesters[i]
            prev_code = str(prev_sem.get("code") or prev_sem.get("id") or "")
            if not prev_code: continue
            
            logger.info(f"Sync: Fallback GPA check for {student.full_name}, sem: {prev_code}")
            prev_gpa = await HemisService.get_student_performance(student.hemis_token, student_id=student.id, semester_code=prev_code)
            if prev_gpa > 0:
                gpa = prev_gpa
                logger.info(f"Sync: Found valid GPA {gpa} in semester {prev_code}")
                break

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

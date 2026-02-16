import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentCache, TgAccount, StudentNotification
from services.hemis_service import HemisService
from services.notification_service import NotificationService
from bot import bot

import asyncio
import logging
from celery_app import app as celery_app

logger = logging.getLogger(__name__)

# @celery_app.task(name="check_new_grades")
# def run_check_new_grades():
#     """Celery task wrapper for grade checks"""
#     return asyncio.run(check_new_grades())

@celery_app.task(name="send_student_welcome_report")
def run_send_welcome_report(student_id: int):
    """Celery task wrapper for welcome report"""
    return asyncio.run(send_welcome_report(student_id))

async def check_new_grades():
    logger.info("🔍 Checking for new grades...")
    async with AsyncSessionLocal() as session:
        # Get active students with tokens
        stmt = select(Student).where(Student.is_active == True, Student.hemis_token.is_not(None)).options(selectinload(Student.tg_accounts))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        for student in students:
            try:
                # 1. Fetch Fresh Data (Network Call)
                # We don't pass student_id to force fresh fetch
                # We use student's current stored semester name/code logic if possible, or just default (current)
                # Usually default is best for "Current Semester" grades.
                fresh_subjects = await HemisService.get_student_subject_list(student.hemis_token)
                
                if not fresh_subjects:
                    continue

                # 2. Get Cached Data
                # We need to guess the "key". HemisService uses "subjects_{semester_code}" or "subjects_all".
                # If fresh_subjects returns data, it's for specific semester (usually current).
                # We can extract semester code from the first item in fresh_subjects if available.
                sem_code = None
                if fresh_subjects and isinstance(fresh_subjects[0], dict):
                     semester = fresh_subjects[0].get("semester", {})
                     sem_code = str(semester.get("code") or semester.get("id") or "")
                
                key = f"subjects_{sem_code}" if sem_code else "subjects_all"
                
                cache_entry = await session.scalar(select(StudentCache).where(StudentCache.student_id == student.id, StudentCache.key == key))
                cached_data = cache_entry.data if cache_entry else []
                
                # 3. Compare
                changes = [] # List of strings to notify
                
                # Convert cached list to dict by subject ID for O(1) lookup
                # ID extraction: curriculumSubject -> subject -> id/name
                cached_map = {}
                for s in cached_data:
                    curr_subj = s.get("curriculumSubject", {})
                    subj_data = curr_subj.get("subject", {}) or s.get("subject", {})
                    sid = str(subj_data.get("id") or subj_data.get("name"))
                    cached_map[sid] = s
                
                for fresh_subj in fresh_subjects:
                    curr_subj = fresh_subj.get("curriculumSubject", {})
                    subj_data = curr_subj.get("subject", {}) or fresh_subj.get("subject", {})
                    
                    subj_id = str(subj_data.get("id") or subj_data.get("name"))
                    subj_name = subj_data.get("name") or "Noma'lum fan"
                    
                    old_subj = cached_map.get(subj_id)
                    
                    if not old_subj:
                        # New subject? Unlikely mid-semester, but possible.
                        # Check if it has grades > 0
                        is_jmcu = (student.hemis_login[:3] == "395") if student.hemis_login else False
                        parsed_fresh = HemisService.parse_grades_detailed(fresh_subj, skip_conversion=not is_jmcu)
                        if parsed_fresh["raw_total"] > 0:
                            changes.append(f"🆕 <b>{subj_name}</b> fanidan baholar chiqdi!")
                        continue
                        
                    # Compare Grades
                    is_jmcu = (student.hemis_login[:3] == "395") if student.hemis_login else False
                    parsed_fresh = HemisService.parse_grades_detailed(fresh_subj, skip_conversion=not is_jmcu)
                    parsed_old = HemisService.parse_grades_detailed(old_subj, skip_conversion=not is_jmcu)
                    
                    # ON Check
                    if parsed_fresh["ON"]["raw"] > parsed_old["ON"]["raw"]:
                         changes.append(f"📈 <b>{subj_name}</b>: Oraliq Nazorat (ON) dan <b>{parsed_fresh['ON']['raw']}</b> ball qo'yildi!")
                    
                    # YN Check
                    if parsed_fresh["YN"]["raw"] > parsed_old["YN"]["raw"]:
                         changes.append(f"🎓 <b>{subj_name}</b>: Yakuniy Nazorat (YN) dan <b>{parsed_fresh['YN']['raw']}</b> ball qo'yildi!")

                # 4. Notify & Update
                if changes:
                    # Notify via Telegram
                    tg_id = None
                    if student.tg_accounts:
                        tg_id = student.tg_accounts[0].telegram_id
                    
                    if tg_id:
                        msg = "⚡️ <b>Yangi Baholar!</b>\n\n" + "\n".join(changes)
                        try:
                            await bot.send_message(tg_id, msg, parse_mode="HTML")
                            logger.info(f"Notified {student.full_name} about grades.")
                        except Exception as e:
                            logger.error(f"Failed to notify {student.full_name}: {e}")
                    
                    # Create Notification in DB for Mobile App
                    try:
                        notif_body = "\n".join(changes).replace("<b>", "").replace("</b>", "")
                        new_notif = StudentNotification(
                            student_id=student.id,
                            title="⚡️ Yangi Baholar!",
                            body=notif_body,
                            type="grade",
                            is_read=False
                        )
                        session.add(new_notif)
                    except Exception as e:
                        logger.error(f"Failed to create app notification: {e}")
                    
                    # [NEW] Push Notification
                    if student.fcm_token:
                        await NotificationService.send_push(
                            token=student.fcm_token,
                            title="⚡️ Yangi Baholar!",
                            body=notif_body,
                            data={"type": "grade"}
                        )
                    
                    # Update Cache in DB
                    if cache_entry:
                        cache_entry.data = fresh_subjects
                    else:
                        new_cache = StudentCache(student_id=student.id, key=key, data=fresh_subjects)
                        session.add(new_cache)
                    
                    await session.commit()
                else:
                    # Update cache anyway to keep it fresh? 
                    # Yes, logic dictates cache should reflect latest state to avoid false positives later if structure changes.
                    # But if no grade change, JSON diff might be trivial.
                    # Let's simple check if we should update.
                    # Actually, for "First Run", if cache doesn't exist, we should save it but NOT notify (or maybe notify "Monitoring started").
                    # User asked for "yangi baho".
                    # If cache_entry is None, it's the first run.
                    if not cache_entry:
                         new_cache = StudentCache(student_id=student.id, key=key, data=fresh_subjects)
                         session.add(new_cache)
                         await session.commit()
                    elif fresh_subjects != cached_data:
                         # Update invisible changes
                         cache_entry.data = fresh_subjects
                         await session.commit()

            except Exception as e:
                logger.error(f"Grade check error for student {student.id}: {e}")

async def send_welcome_report(student_id: int):
    """
    Sends an initial grade report to a newly registered student.
    """
    async with AsyncSessionLocal() as session:
        # Load student with TgAccount
        stmt = select(Student).where(Student.id == student_id).options(selectinload(Student.tg_accounts))
        result = await session.execute(stmt)
        student = result.scalar_one_or_none()
        
        if not student or not student.tg_accounts:
            return

        tg_id = student.tg_accounts[0].telegram_id
        
        try:
            # Fetch fresh subjects
            subjects = await HemisService.get_student_subject_list(student.hemis_token)
            if not subjects:
                return

            # Check for YN grades
            is_jmcu = (student.hemis_login[:3] == "395") if student.hemis_login else False
            yn_list = []
            for subj in subjects:
                parsed = HemisService.parse_grades_detailed(subj, skip_conversion=not is_jmcu)
                yn_score = parsed["YN"]["raw"]
                if yn_score > 0:
                    curr_subj = subj.get("curriculumSubject", {})
                    subj_data = curr_subj.get("subject", {}) or subj.get("subject", {})
                    subj_name = subj_data.get("name") or "Noma'lum fan"
                    
                    yn_list.append(f"✅ <b>{subj_name}</b>: {yn_score} ball")

            # Construct Message
            header = "📝 <b>YAKUNIY NAZORAT (YN) HISOBOTI</b>\n\n"
            
            if yn_list:
                body = "Hozirgacha quyidagi fanlardan Yakuniy baholar qo'yilgan:\n\n" + "\n".join(yn_list)
            else:
                body = "Hozirgacha hech qaysi fandan Yakuniy baho (YN) qo'yilmagan."
            
            footer = (
                "\n\n────────────────\n"
                "🚀 <b>MONITORING BOŞLANDI:</b>\n"
                "Bot endi baholaringizni doimiy kuzatib boradi.\n"
                "Yangi baho chiqishi bilan sizga darhol xabar beramiz!\n\n"
                "<i>Siz faqat kuting, bot o'zi xabar beradi!</i> 😎"
            )
            
            full_msg = header + body + footer
            
            await bot.send_message(tg_id, full_msg, parse_mode="HTML")
            logger.info(f"Sent welcome report to {student.full_name} ({tg_id})")
            
        except Exception as e:
            logger.error(f"Failed to send welcome report to {student.full_name}: {e}")

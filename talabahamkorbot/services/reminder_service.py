import logging
import asyncio
import time
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache, TgAccount, Student
from services.hemis_service import HemisService
from bot import bot

logger = logging.getLogger(__name__)

async def sync_all_students_weekly_schedule():
    """
    Fetches schedule for ALL active students for the current week.
    Scheduled to run: Monday 06:00.
    """
    logger.info("🔄 Starting Weekly Schedule Sync...")
    
    # Calculate Week Range (Monday to Sunday)
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday()) # Monday
    end_of_week = start_of_week + timedelta(days=6) # Sunday
    
    s_date = start_of_week.strftime("%Y-%m-%d")
    e_date = end_of_week.strftime("%Y-%m-%d")
    
    async with AsyncSessionLocal() as session:
        # Fetch students with Telegram accounts (Active users)
        stmt = select(Student).join(TgAccount).options(selectinload(Student.tg_accounts))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        logger.info(f"Syncing schedule for {len(students)} students ({s_date} to {e_date})")
        
        count = 0
        for student in students:
            if not student.hemis_token: continue
            
            try:
                # Direct Fetch & Cache (Logic inside HemisService or manual here)
                # We use HemisService.get_student_schedule which returns list but DOES NOT cache automatically unless we wrap it
                # Using get_student_schedule (dates) endpoint
                data = await HemisService.get_student_schedule(student.hemis_token, s_date, e_date)
                
                if data:
                    # Manually Update Cache
                    key = "schedule_weekly"
                    
                    # Check existing
                    q = select(StudentCache).where(
                        StudentCache.student_id == student.id, 
                        StudentCache.key == key
                    )
                    cache = (await session.execute(q)).scalar_one_or_none()
                    
                    if cache:
                        cache.data = data
                        cache.updated_at = datetime.utcnow()
                    else:
                        session.add(StudentCache(student_id=student.id, key=key, data=data))
                    
                    count += 1
            except Exception as e:
                logger.error(f"Failed to sync schedule for {student.id}: {e}")
            
            # Rate limit
            await asyncio.sleep(0.2)
        
        await session.commit()
        logger.info(f"✅ Weekly Schedule Synced for {count} students.")


async def run_lesson_reminders():
    """
    # Checks cached weekly schedule for lessons starting SOON (10 mins msg warning).
    # Scheduled to run at: 08:20, 09:50, 11:40, 13:20, 14:50, 16:20
    # Logic: Look for lessons starting in next 5-15 minutes.
    try:
        now = datetime.now()
        # Look ahead window:
        # 08:20 -> 08:30 (10 min)
        # So we look for lessons starting in [now+5min, now+15min] range.
        
        target_time_start = now + timedelta(minutes=5)
        target_time_end = now + timedelta(minutes=15)
        
        # logger.info(f"Checking reminders window: {target_time_start.strftime('%H:%M')} - {target_time_end.strftime('%H:%M')}")

        async with AsyncSessionLocal() as session:
            # Fetch ALL "schedule_weekly" caches
            stmt = select(StudentCache).where(StudentCache.key == "schedule_weekly")
            result = await session.execute(stmt)
            caches = result.scalars().all()
            
            if not caches: return

            # Map Student -> TG
            student_ids = [c.student_id for c in caches]
            if not student_ids: return

            stmt_tg = select(TgAccount).where(TgAccount.student_id.in_(student_ids))
            res_tg = await session.execute(stmt_tg)
            tg_map = {tg.student_id: tg.telegram_id for tg in res_tg.scalars().all()}
            
            count_sent = 0
            
            for cache in caches:
                tg_id = tg_map.get(cache.student_id)
                if not tg_id: continue
                
                data = cache.data
                if not isinstance(data, list): continue
                
                for lesson in data:
                    try:
                        # Parse
                        l_date_ts = lesson.get("lesson_date")
                        l_pair = lesson.get("lessonPair", {})
                        start_time_str = l_pair.get("start_time") 
                        
                        if not l_date_ts or not start_time_str: continue
                        
                        date_obj = datetime.fromtimestamp(l_date_ts)
                        h, m = map(int, start_time_str.split(":"))
                        lesson_start = date_obj.replace(hour=h, minute=m, second=0, microsecond=0)
                        
                        # Check strict window (approx 30 mins from now)
                        if target_time_start <= lesson_start <= target_time_end:
                            # TRIGGER
                            subject = lesson.get("subject", {}).get("name", "Dars")
                            auditorium = lesson.get("auditorium", {}).get("name", "Xona?")
                            building = lesson.get("auditorium", {}).get("building", {}).get("name", "")
                            
                            # Clean Building Name
                            if "O'zbekiston jurnalistika" in building:
                                building = "UzJOKU"
                                
                            if building: auditorium += f" ({building})"
                            
                            teacher = lesson.get("employee", {}).get("name", "")
                            
                            t = start_time_str
                            
                            remaining_min = int((lesson_start - now).total_seconds() / 60)
                            
                            # Updated Template: Room First, Added Teacher
                            msg = (
                                f"🔔 <b>DARS ESLATMASI!</b>\n"
                                f"⏳ (Boshlanishiga {remaining_min} daqiqa qoldi)\n\n"
                                f"🚪 <b>{auditorium}</b>\n"
                                f"📚 <b>{subject}</b>\n"
                            )
                            
                            if teacher:
                                msg += f"👤 <i>{teacher}</i>\n"
                                
                            msg += (
                                f"🕐 <b>{t}</b> ({l_pair.get('name')}-para)\n\n"
                                f"<i>Harakatni boshlang!</i> 🏃‍♂️"
                            )
                            
                            try:
                                await bot.send_message(chat_id=tg_id, text=msg)
                                count_sent += 1
                            except Exception as e:
                                logger.error(f"Send fail {tg_id}: {e}")
                                
                    except: continue

            if count_sent > 0:
                logger.info(f"✅ Sent {count_sent} reminders (Scheduled Check).")

    except Exception as e:
        logger.exception("Reminder Check Error")

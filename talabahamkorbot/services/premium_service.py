import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, TakenUsername, StudentNotification
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class PremiumService:
    @classmethod
    async def check_premium_expiries(cls):
        """
        Background task to handle premium grace periods:
        Day 0: Expiry notification.
        Day 3: Feature closure notification.
        Day 7: Username removal & Premium status update.
        """
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            
            # 1. Day 0: Just expired today
            # (premium_expiry between yesterday 23:59 and today 23:59)
            # Simplified: expired in last 24h
            day0_stmt = select(Student).where(
                Student.is_premium == True,
                Student.premium_expiry <= now,
                Student.premium_expiry > now - timedelta(days=1)
            )
            day0_res = await session.execute(day0_stmt)
            day0_students = day0_res.scalars().all()
            
            for s in day0_students:
                await cls.notify_expiry(s, session, "⚠️ Obuna muddati tugadi", 
                    "Sizning Premium obunangiz bugun tugadi. 3 kundan keyin AI va ijtimoiy funksiyalar yopiladi.")

            # 2. Day 3: Features closed
            day3_stmt = select(Student).where(
                Student.is_premium == True,
                Student.premium_expiry <= now - timedelta(days=3),
                Student.premium_expiry > now - timedelta(days=4)
            )
            day3_res = await session.execute(day3_stmt)
            day3_students = day3_res.scalars().all()
            
            for s in day3_students:
                await cls.notify_expiry(s, session, "🚫 Premium funksiyalar yopildi", 
                    "AI va ijtimoiy faollik funksiyalari to'xtatildi. 4 kundan so'ng @username ham o'chiriladi.")

            # 3. Day 7: Username removal
            day7_stmt = select(Student).where(
                Student.is_premium == True,
                Student.premium_expiry <= now - timedelta(days=7)
            )
            day7_res = await session.execute(day7_stmt)
            day7_students = day7_res.scalars().all()
            
            for s in day7_students:
                logger.info(f"Removing premium and username for student {s.id}")
                s.is_premium = False
                
                if s.username:
                    username_entry = await session.scalar(select(TakenUsername).where(TakenUsername.student_id == s.id))
                    if username_entry:
                        await session.delete(username_entry)
                    s.username = None
                
                await cls.notify_expiry(s, session, "❌ Premium va Username o'chirildi", 
                    "Imtiyozli 7 kunlik muddat tugadi. Sizning @username barcha uchun ochiq holga keldi.")

            await session.commit()

    @classmethod
    async def notify_expiry(cls, student: Student, session, title: str, body: str):
        """Helper to create DB notification and send push"""
        notif = StudentNotification(
            student_id=student.id,
            title=title,
            body=body,
            type="premium_alert"
        )
        session.add(notif)
        
        if student.fcm_token:
            await NotificationService.send_push(student.fcm_token, title, body)

async def run_premium_checker():
    """Entry point for scheduler/celery"""
    await PremiumService.check_premium_expiries()

import asyncio
import logging
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student
from services.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_broadcast():
    logger.info("Starting Security Broadcast...")
    
    async with AsyncSessionLocal() as session:
        # 1. Fetch Students with FCM Tokens
        result = await session.execute(select(Student).where(Student.fcm_token.isnot(None)))
        students = result.scalars().all()
        
        logger.info(f"Fonund {len(students)} students with push tokens.")
        
        success_push = 0
        for student in students:
            try:
                # Send Push
                await NotificationService.send_push(
                    token=student.fcm_token,
                    title="🛡 Xavfsizlik Yangilanishi",
                    body="Iltimos, ilovadan chiqib qaytadan kiring.",
                    data={"type": "force_logout", "action": "logout"} # Custom payload for app
                )
                success_push += 1
            except Exception as e:
                logger.error(f"Push failed for {student.id}: {e}")
            
            # Rate limit prevention
            if success_push % 100 == 0:
                await asyncio.sleep(1)

        if success_push > 0:
            logger.info(f"✅ Push Notification Sent: {success_push}/{len(students)}")
        else:
            logger.warning("No push notifications were sent. Check FCM tokens.")

if __name__ == "__main__":
    asyncio.run(send_broadcast())

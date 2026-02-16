import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentNotification

async def debug_notification():
    async with AsyncSessionLocal() as db:
        print("--- DEBUGGING NOTIFICATION ---")
        
        # 1. Get a student
        target = await db.scalar(select(Student).limit(1))
        if not target:
            print("No students found.")
            return

        print(f"Target: {target.id}")

        # 2. Try adding Notification with type='social'
        try:
            print("Creating notification with type='social'...")
            notif = StudentNotification(
                student_id=target.id,
                title="Test Title",
                body="Test Body",
                type="social" 
            )
            db.add(notif)
            print("Added to session. Flushing...")
            await db.flush() # Should trigger DB error if column missing
            print("Flush success.")
            await db.commit()
            print("Commit success.")
        except Exception as e:
            print(f"FAILED: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(debug_notification())

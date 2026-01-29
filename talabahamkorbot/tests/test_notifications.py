import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentNotification
from sqlalchemy import select

async def main():
    print("Testing Notification System...")
    async with AsyncSessionLocal() as session:
        # Get a student
        student = await session.scalar(select(Student).limit(1))
        if not student:
            print("No student found.")
            return

        print(f"Creating notification for {student.full_name}...")
        
        notif = StudentNotification(
            student_id=student.id,
            title="Test Notification",
            body="This is a test notification from the backend verification script.",
            type="info"
        )
        session.add(notif)
        await session.commit()
        
        print("✅ Notification created!")
        
        # Verify read
        stmt = select(StudentNotification).where(StudentNotification.student_id == student.id)
        result = await session.execute(stmt)
        notifs = result.scalars().all()
        
        print(f"User has {len(notifs)} notifications.")
        for n in notifs:
            print(f"- [{n.id}] {n.title}: {n.body}")

if __name__ == "__main__":
    asyncio.run(main())

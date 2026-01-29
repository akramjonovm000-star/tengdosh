
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import StudentNotification, Student
from sqlalchemy import select, desc

async def check():
    async with AsyncSessionLocal() as session:
        stmt = select(StudentNotification).order_by(desc(StudentNotification.created_at)).limit(10)
        result = await session.execute(stmt)
        notifs = result.scalars().all()
        
        print(f"Found {len(notifs)} recent notifications:")
        for n in notifs:
            print(f"ID: {n.id}, StudentID: {n.student_id}, Title: {n.title}, Created: {n.created_at}")
            # Check if student exists
            s = await session.get(Student, n.student_id)
            print(f"  Student exists: {s is not None}")

if __name__ == "__main__":
    asyncio.run(check())

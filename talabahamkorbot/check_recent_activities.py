import asyncio
from sqlalchemy import select, desc
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity, Student

async def main():
    async with AsyncSessionLocal() as session:
        # List last 10 activities
        stmt = select(UserActivity).order_by(desc(UserActivity.created_at)).limit(10)
        result = await session.execute(stmt)
        activities = result.scalars().all()

        print(f"\n--- Recent Activities (Last 10) ---")
        for act in activities:
            student = await session.get(Student, act.student_id)
            s_name = student.full_name if student else "Unknown"
            print(f"ID: {act.id} | Date: {act.created_at} | Status: {act.status} | Student: {act.student_id} ({s_name}) | Name: {act.name}")

if __name__ == "__main__":
    asyncio.run(main())

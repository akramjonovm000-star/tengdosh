import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity, Student

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Total count of activities
        count = await session.scalar(select(func.count(UserActivity.id)))
        print(f"Total Activities in DB: {count}")

        # 2. List ALL activities (Limit 50) to see if ANY exist for anyone
        # This helps check if table was wiped or if it's just this user
        stmt = select(UserActivity).order_by(UserActivity.id.desc()).limit(50)
        result = await session.execute(stmt)
        activities = result.scalars().all()

        print("\n--- Latest 50 Activities ---")
        for act in activities:
            s = await session.get(Student, act.student_id)
            s_name = s.full_name if s else "UNKNOWN STUDENT"
            print(f"[{act.id}] Student: {act.student_id} ({s_name}) | Status: {act.status} | Name: {act.name}")

if __name__ == "__main__":
    asyncio.run(main())

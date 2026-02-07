import asyncio
from sqlalchemy import select, delete
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity, Student

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Get Student Info
        student_id = 729
        student = await session.get(Student, student_id)
        if not student:
            print("Student 729 not found!")
            return

        print(f"Student: {student.full_name} (ID: {student.id})")

        # 2. List Activities
        stmt = select(UserActivity).where(UserActivity.student_id == student_id)
        result = await session.execute(stmt)
        activities = result.scalars().all()

        print(f"\nFound {len(activities)} activities:")
        for act in activities:
            print(f"[{act.id}] Date: {act.created_at} | Status: {act.status} | Name: {act.name}")
            
            # 3. Cleanup Test Activity
            if "Test Activity from Script" in act.name:
                print(f" -> Deleting Test Activity: {act.id}")
                await session.delete(act)
        
        await session.commit()
        print("\nCleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())

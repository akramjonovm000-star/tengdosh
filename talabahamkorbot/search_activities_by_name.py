import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity, UserActivityImage

async def main():
    async with AsyncSessionLocal() as session:
        # Search for students with "Muhammadali" or "Akramjonov"
        print("--- Searching for all activities by Name ---")
        stmt = (
            select(UserActivity, Student.full_name)
            .join(Student, UserActivity.student_id == Student.id)
            .where(
                (Student.full_name.ilike("%Muhammadali%")) | 
                (Student.full_name.ilike("%Akramjonov%"))
            )
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        print(f"Found {len(rows)} activities matching name search.")
        for act, s_name in rows:
            print(f"[{act.id}] Student: {s_name} (ID: {act.student_id}) | Name: {act.name} | Status: {act.status} | Created: {act.created_at}")

        # Also search by Staff ID 62 just in case
        print("\n--- Searching for activities with student_id = 62 ---")
        stmt_62 = select(UserActivity).where(UserActivity.student_id == 62)
        res_62 = await session.execute(stmt_62)
        acts_62 = res_62.scalars().all()
        print(f"Found {len(acts_62)} activities for ID 62.")
        for a in acts_62:
            print(f"[{a.id}] Name: {a.name} | Status: {a.status} | Created: {a.created_at}")

if __name__ == "__main__":
    asyncio.run(main())

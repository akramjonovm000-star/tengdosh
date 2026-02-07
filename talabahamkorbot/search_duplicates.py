import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity

async def main():
    async with AsyncSessionLocal() as session:
        # Search for first name "Muhammadali"
        print("--- Searching for students named matches 'Muhammadali' ---")
        stmt = select(Student).where(Student.full_name.ilike("%Muhammadali%"))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        for s in students:
            # Count activities
            stmt_act = select(UserActivity).where(UserActivity.student_id == s.id)
            res_act = await session.execute(stmt_act)
            acts = res_act.scalars().all()
            
            if len(acts) > 0:
                print(f"FOUND: {s.full_name} | ID: {s.id} | Activities: {len(acts)}")
                for a in acts:
                    print(f"   -> {a.name} ({a.status}) - {a.date}")
            else:
                 pass
                 # print(f"Student: {s.full_name} | ID: {s.id} | No activities")

if __name__ == "__main__":
    asyncio.run(main())

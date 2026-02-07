import asyncio
from sqlalchemy import select, func, desc
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount, UserActivity, UserActivityImage

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Search for students with "Muhammadali" or "Akramjonov"
        print("--- Searching for students with 'Muhammadali' or 'Akramjonov' ---")
        stmt = select(Student).where(
            (Student.full_name.ilike("%Muhammadali%")) | 
            (Student.full_name.ilike("%Akramjonov%"))
        )
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        for s in students:
            print(f"Student ID: {s.id} | Name: {s.full_name} | Login: {s.hemis_login}")
            # Check activities
            act_stmt = select(UserActivity).where(UserActivity.student_id == s.id)
            act_res = await session.execute(act_stmt)
            acts = act_res.scalars().all()
            print(f"  -> Activity count: {len(acts)}")
            for a in acts:
                print(f"     ID: {a.id} | Name: {a.name} | Status: {a.status} | Created: {a.created_at}")
            
            # Check TG account
            tg_stmt = select(TgAccount).where(TgAccount.student_id == s.id)
            tg_res = await session.execute(tg_stmt)
            tgs = tg_res.scalars().all()
            for tg in tgs:
                print(f"  -> Linked TG ID: {tg.telegram_id}")

        # 2. Check MOST RECENT activities in the whole system
        print("\n--- Recent Activities (Global) ---")
        stmt = select(UserActivity).order_by(desc(UserActivity.created_at)).limit(10)
        result = await session.execute(stmt)
        for a in result.scalars():
            s = await session.get(Student, a.student_id)
            s_name = s.full_name if s else "Unknown"
            print(f"Activity ID: {a.id} | Student: {s_name} (ID: {a.student_id}) | Name: {a.name} | Status: {a.status}")

        # 3. Check for any activity with name containing "Muhammadali" or "Akramjonov" (just in case they put it in the name)
        print("\n--- Activities with search terms in name/description ---")
        stmt = select(UserActivity).where(
            (UserActivity.name.ilike("%Muhammadali%")) | 
            (UserActivity.description.ilike("%Muhammadali%")) |
            (UserActivity.name.ilike("%Akramjonov%")) |
            (UserActivity.description.ilike("%Akramjonov%"))
        )
        result = await session.execute(stmt)
        for a in result.scalars():
            print(f"Activity ID: {a.id} | Student ID: {a.student_id} | Name: {a.name}")

if __name__ == "__main__":
    asyncio.run(main())

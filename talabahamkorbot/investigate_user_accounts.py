import asyncio
from sqlalchemy import select, or_
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount, UserActivity

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Search for students with name "Akramjonov"
        print("--- Searching for students named 'Akramjonov' ---")
        stmt = select(Student).where(Student.full_name.ilike("%Akramjonov%"))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        for s in students:
            print(f"Student: {s.full_name} | ID: {s.id} | Hemis ID: {s.hemis_id} | Login: {s.hemis_login}")
            
            # Manual count for safety if func is issue
            act_stmt = select(UserActivity).where(UserActivity.student_id == s.id)
            act_res = await session.execute(act_stmt)
            acts = act_res.scalars().all()
            print(f"   -> Activities count: {len(acts)}")
            for a in acts:
                print(f"      - [{a.id}] {a.name} ({a.status})")

            # Check linked TG accounts
            tg_stmt = select(TgAccount).where(TgAccount.student_id == s.id)
            tg_res = await session.execute(tg_stmt)
            tgs = tg_res.scalars().all()
            for tg in tgs:
                print(f"   -> Linked TG ID: {tg.telegram_id}")

if __name__ == "__main__":
    asyncio.run(main())

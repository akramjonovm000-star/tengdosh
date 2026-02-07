import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount, Staff, User

async def main():
    async with AsyncSessionLocal() as session:
        tg_id = 387178074
        print(f"--- Investigating TG ID: {tg_id} ---")
        
        stmt = select(TgAccount).where(TgAccount.telegram_id == tg_id)
        result = await session.execute(stmt)
        tg_acc = result.scalar_one_or_none()
        
        if tg_acc:
            print(f"Linked Student ID: {tg_acc.student_id}")
            print(f"Linked Staff ID: {tg_acc.staff_id}")
            print(f"Linked User ID: {tg_acc.user_id}")
            
            if tg_acc.staff_id:
                s = await session.get(Staff, tg_acc.staff_id)
                print(f"Staff Name: {s.full_name} | Role: {s.role}")
            
            if tg_acc.user_id:
                u = await session.get(User, tg_acc.user_id)
                print(f"User Name: {u.full_name} | Username: {u.username}")
        else:
            print("No TgAccount found for this TG ID!")

        # Search Staff by name
        print("\n--- Searching Staff by name 'Akramjonov' ---")
        stmt = select(Staff).where(Staff.full_name.ilike("%Akramjonov%"))
        result = await session.execute(stmt)
        for s in result.scalars():
             print(f"Staff ID: {s.id} | Name: {s.full_name} | Role: {s.role}")

if __name__ == "__main__":
    asyncio.run(main())

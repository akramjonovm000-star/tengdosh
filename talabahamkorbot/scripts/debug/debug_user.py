import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TgAccount, Faculty

async def check_user():
    async with AsyncSessionLocal() as session:
        tg_id = 2086982893
        print(f"Checking User TG ID: {tg_id}")
        
        acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
        if acc and acc.staff_id:
            staff = await session.get(Staff, acc.staff_id)
            print(f"Staff Name: {staff.full_name}")
            print(f"Role: {staff.role}")
            print(f"Faculty ID: {staff.faculty_id}")
            if staff.faculty_id:
                fac = await session.get(Faculty, staff.faculty_id)
                print(f"Faculty Name: {fac.name if fac else 'None'}")
        else:
            print("User not found or not staff")

if __name__ == "__main__":
    asyncio.run(check_user())

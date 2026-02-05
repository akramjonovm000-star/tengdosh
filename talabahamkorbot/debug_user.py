import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TgAccount, StaffRole

async def check():
    async with AsyncSessionLocal() as s:
        print("Checking for User ID: 7476703866")
        r1 = await s.execute(select(Staff).where(Staff.telegram_id == 7476703866))
        s1 = r1.scalars().all()
        if not s1:
            print("No Staff record found.")
        for dev in s1:
            print(f"Staff: ID={dev.id}, Name={dev.full_name}, Role={dev.role}, Active={dev.is_active}")
        
        r2 = await s.execute(select(TgAccount).where(TgAccount.telegram_id == 7476703866))
        t1 = r2.scalars().all()
        if not t1:
            print("No TgAccount record found.")
        for acc in t1:
            print(f"TgAccount: ID={acc.id}, Role={acc.current_role}, StaffID={acc.staff_id}")

if __name__ == "__main__":
    asyncio.run(check())

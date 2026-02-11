import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Staff

async def check_staff():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Staff).where(Staff.university_id == None))
        staff_list = res.scalars().all()
        print(f"Staff with UniID=None: {len(staff_list)}")
        for s in staff_list:
             print(f"ID: {s.id}, Name: {s.full_name}, Role: {getattr(s, 'role', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(check_staff())

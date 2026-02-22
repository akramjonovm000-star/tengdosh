import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff

async def check_staff():
    async with AsyncSessionLocal() as db:
        stmt = select(Staff).where(Staff.university_id == None)
        staffs = (await db.execute(stmt)).scalars().all()
        print(f"Count of staff with NULL university_id: {len(staffs)}")
        for s in staffs[:10]:
            print(f"ID: {s.id}, Name: {s.full_name}, Role: {s.role}")

if __name__ == '__main__':
    asyncio.run(check_staff())

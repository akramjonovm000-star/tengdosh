import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff

async def list_staffs():
    async with AsyncSessionLocal() as db:
        stmt = select(Staff).order_by(Staff.id.desc()).limit(15)
        staffs = (await db.execute(stmt)).scalars().all()
        for s in staffs:
            print(f"ID: {s.id}, Name: {s.full_name}, Role: {s.role}, UniID: {s.university_id}, FacID: {s.faculty_id}")

if __name__ == '__main__':
    asyncio.run(list_staffs())

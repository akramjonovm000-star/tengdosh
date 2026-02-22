import asyncio
import json
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Staff, Student

async def check_dean_stats():
    async with AsyncSessionLocal() as db:
        # Get staff users
        stmt = select(Staff).where(Staff.role.ilike('%dekan%'))
        staffs = (await db.execute(stmt)).scalars().all()
        for s in staffs:
            if s.faculty_id:
                count = await db.scalar(select(func.count(Student.id)).where(Student.faculty_id == s.faculty_id))
                print(f"Dean: {s.full_name}, Fac_id: {s.faculty_id}, Students in DB: {count}")
            else:
                print(f"Dean: {s.full_name}, Fac_id: None")

if __name__ == '__main__':
    asyncio.run(check_dean_stats())

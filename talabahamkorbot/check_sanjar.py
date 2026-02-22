import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Staff).where(Staff.full_name.ilike('%Sanjar%')))
        for s in res.scalars():
            print(f"ID: {s.id}, Name: {s.full_name}, uni: {s.university_id}, fac: {s.faculty_id}, role: {s.role}")

asyncio.run(run())

import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Student.faculty_id).distinct())
        vals = [r[0] for r in res.all()]
        print(f"Distinct faculty_id in Student table: {vals}")

if __name__ == "__main__":
    asyncio.run(check())

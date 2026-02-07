import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Student.id, Student.full_name).where(Student.full_name.ilike('%Demo%')))
        print("Demo students:", res.all())
        
        res = await db.execute(select(Student.id, Student.full_name).where(Student.full_name.ilike('%Test%')))
        print("Test students:", res.all())

if __name__ == "__main__":
    asyncio.run(check())

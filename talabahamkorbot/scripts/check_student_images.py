import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Student.id, Student.full_name, Student.image_url).limit(20))
        students = res.all()
        print("Student images:")
        for s in students:
            print(f"ID {s.id}: {s.full_name} -> {s.image_url}")

if __name__ == '__main__':
    asyncio.run(check())

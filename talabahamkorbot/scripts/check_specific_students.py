import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as db:
        names = ["Javohirxon Rahimxonov", "Muxammadali Akramjonov"]
        for name in names:
            res = await db.execute(select(Student.id, Student.full_name, Student.image_url).where(Student.full_name.ilike(f"%{name.split()[0]}%")))
            for s in res.all():
                print(f"ID {s.id}: {s.full_name} -> {s.image_url}")

if __name__ == '__main__':
    asyncio.run(check())

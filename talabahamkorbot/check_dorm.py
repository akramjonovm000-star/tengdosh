import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def check_dorm_students():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Student.accommodation_name)
            .where(Student.accommodation_name.ilike('%turar joyi%'))
            .limit(5)
        )
        names = result.scalars().all()
        print(f"Dormitory names found: {names}")

if __name__ == "__main__":
    asyncio.run(check_dorm_students())

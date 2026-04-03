import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def check_accommodations():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student.accommodation_name).where(Student.accommodation_name.isnot(None)).limit(10))
        names = result.scalars().all()
        print(f"Accommodation names found: {names}")

if __name__ == "__main__":
    asyncio.run(check_accommodations())

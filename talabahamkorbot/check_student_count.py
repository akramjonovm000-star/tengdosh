import asyncio
from sqlalchemy import func, select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count(Student.id)))
        print(f"Current Student Count: {count}")

if __name__ == "__main__":
    asyncio.run(main())

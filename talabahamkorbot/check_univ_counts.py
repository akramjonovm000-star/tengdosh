import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        print("--- University Name Distribution ---")
        stmt = select(Student.university_name, func.count(Student.id)).group_by(Student.university_name)
        result = await session.execute(stmt)
        items = result.all()
        for univ, count in items:
            print(f"- {univ}: {count}")

if __name__ == "__main__":
    asyncio.run(main())

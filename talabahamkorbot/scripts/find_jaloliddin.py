import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def check_jaloliddin():
    async with AsyncSessionLocal() as db:
        query = select(Student).where(Student.full_name.ilike("%Jaloliddin Ramazanov%"))
        result = await db.execute(query)
        students = result.scalars().all()
        
        print(f"Found {len(students)} students matching 'Jaloliddin Ramazanov':")
        for s in students:
            print(f"ID: {s.id}, HemisID: {s.hemis_id}, Username: {s.username}, Role: {s.hemis_role}")

if __name__ == "__main__":
    asyncio.run(check_jaloliddin())


import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student).limit(10))
        students = result.scalars().all()
        print(f"Found {len(students)} students.")
        for s in students:
            print(f"ID: {s.id}, Name: {s.full_name}, FacName: {s.faculty_name}, FacID: {s.faculty_id}, Spec: {s.specialty_name}")

if __name__ == "__main__":
    asyncio.run(check())

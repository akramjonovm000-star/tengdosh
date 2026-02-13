import asyncio
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student.faculty_name, Student.faculty_id).distinct())
        faculties = result.all()
        print("Faculties found:")
        for name, fid in faculties:
            print(f"ID: {fid}, Name: {name}")

if __name__ == "__main__":
    asyncio.run(main())

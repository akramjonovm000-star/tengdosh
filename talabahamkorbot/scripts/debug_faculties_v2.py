
import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as session:
        stmt = select(Student.faculty_id, Student.faculty_name, func.count()).group_by(Student.faculty_id, Student.faculty_name)
        result = await session.execute(stmt)
        print("Faculty distribution in DB:")
        for row in result.all():
            print(f"ID: {row[0]}, Name: {row[1]}, Count: {row[2]}")

if __name__ == "__main__":
    asyncio.run(main())

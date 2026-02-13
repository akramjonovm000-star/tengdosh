
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select, func

async def run():
    async with AsyncSessionLocal() as session:
        print("Checking for unique (faculty_id, faculty_name) pairs...")
        stmt = select(Student.faculty_id, Student.faculty_name, func.count(Student.id)).group_by(Student.faculty_id, Student.faculty_name)
        result = await session.execute(stmt)
        rows = result.all()
        
        for r in rows:
            print(f"ID: {r[0]}, Name: '{r[1]}', Count: {r[2]}")

if __name__ == "__main__":
    asyncio.run(run())

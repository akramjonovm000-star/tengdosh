
import asyncio
import sys
import os

# Appending path to find modules
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def check_user():
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(Student).where(Student.id == 859))
        if user:
            print(f"ID:{user.id}")
            print(f"UniID:{user.university_id}")
            print(f"FacID:{user.faculty_id}")
            print(f"Spec:{user.specialty_name}")
            print(f"UniName:{user.university_name}")
            print(f"FacName:{user.faculty_name}")
        else:
            print("User 859 not found")

if __name__ == "__main__":
    asyncio.run(check_user())


import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as db:
        s = await db.get(Student, 730)
        if s:
            print(f"ID: {s.id}")
            print(f"Name: {s.full_name}")
            print(f"Group: {s.group_number} (Len: {len(s.group_number) if s.group_number else 0})")
            print(f"Faculty: {s.faculty_name} (Len: {len(s.faculty_name) if s.faculty_name else 0})")
        else:
            print("Student 730 not found")

if __name__ == "__main__":
    asyncio.run(check())

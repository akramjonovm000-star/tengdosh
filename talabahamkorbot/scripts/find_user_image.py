import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        # Search for Akramjonov
        stmt = select(Student).where(Student.full_name.ilike("%Akramjonov%"))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        print(f"Found {len(students)} students matching 'Akramjonov':")
        for s in students:
            print(f"ID: {s.id}")
            print(f"Name: {s.full_name}")
            print(f"Short Name: {s.short_name}")
            print(f"Hemis ID: {s.hemis_id}")
            print(f"Image URL: {s.image_url}")
            print(f"Group: {s.group_number}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())

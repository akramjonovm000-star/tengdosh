
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student
from services.sync_service import sync_student_data

async def main():
    async with AsyncSessionLocal() as session:
        # Get user
        s = await session.scalar(select(Student).where(Student.hemis_login == '395251101411'))
        if not s:
            print("User not found")
            return

        print(f"Syncing data for {s.full_name}...")
        await sync_student_data(session, s.id)
        await session.commit()
        await session.refresh(s)
        
        print(f"Sync Complete.")
        print(f"New GPA: {s.gpa}")
        print(f"Semester: {s.semester_name}")

if __name__ == "__main__":
    asyncio.run(main())

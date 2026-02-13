
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff, Faculty
from sqlalchemy import select, or_

async def run():
    async with AsyncSessionLocal() as session:
        # 1. Find Staff
        print("--- STAFF SEARCH ---")
        stmt_staff = select(Staff).where(or_(Staff.full_name.ilike("%dekanat%"), Staff.full_name.ilike("%demo%")))
        staffs = (await session.execute(stmt_staff)).scalars().all()
        for s in staffs:
            print(f"ID: {s.id}, Name: {s.full_name}, FacultyID: {s.faculty_id}, Role: {s.role}")

        # 2. Find Faculty
        print("\n--- FACULTY SEARCH ---")
        stmt_fac = select(Faculty)
        faculties = (await session.execute(stmt_fac)).scalars().all()
        for f in faculties:
            print(f"ID: {f.id}, Name: {f.name}")

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        print(f"Error: {e}")

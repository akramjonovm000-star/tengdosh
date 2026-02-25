import asyncio
import sys
import os
sys.path.append(os.getcwd())
from database.db_connect import AsyncSessionLocal
from database.models import Staff, StaffRole
from sqlalchemy.future import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Staff).where(Staff.role == StaffRole.TYUTOR).limit(3))
        tutors = result.scalars().all()
        for t in tutors:
            print(f"Name: {t.full_name}, EmpID: {t.employee_id_number}")

asyncio.run(main())

import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import select
from database.db_connect import engine, AsyncSessionLocal
from database.models import Staff, Faculty

async def check_jshshir():
    async with AsyncSessionLocal() as session:
        jshshir = "41611843330020"
        print(f"Checking JSHSHIR: {jshshir}")
        
        staff = await session.scalar(select(Staff).where(Staff.jshshir == jshshir))
        
        if staff:
            print(f"FOUND: {staff.full_name}")
            print(f"Role: {staff.role}")
            print(f"Faculty ID: {staff.faculty_id}")
            if staff.faculty_id:
                fac = await session.get(Faculty, staff.faculty_id)
                print(f"Faculty Name: {fac.name if fac else 'None'}")
        else:
            print("NOT FOUND in DB")

if __name__ == "__main__":
    asyncio.run(check_jshshir())

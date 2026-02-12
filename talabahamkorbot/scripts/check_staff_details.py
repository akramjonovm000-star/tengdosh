import asyncio
import os
import sys

# Add project root
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

async def check_staff(staff_id):
    async with AsyncSessionLocal() as db:
        staff = await db.get(Staff, staff_id)
        if staff:
            print(f"ID: {staff.id}")
            print(f"Name: {staff.full_name}")
            print(f"Role: {staff.role}")
            print(f"Uni ID: {staff.university_id}")
            print(f"Fac ID: {staff.faculty_id}")
            # print(f"Hemis Role: {getattr(staff, 'hemis_role', 'N/A')}")
        else:
            print(f"Staff {staff_id} not found")

if __name__ == "__main__":
    asyncio.run(check_staff(80))

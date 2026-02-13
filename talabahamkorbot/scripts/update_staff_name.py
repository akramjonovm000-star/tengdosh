
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff

async def run():
    async with AsyncSessionLocal() as session:
        staff_id = 80
        staff = await session.get(Staff, staff_id)
        
        if staff:
            if "(Jurnalistika)" in staff.full_name:
                print(f"Updating Name for: {staff.full_name}")
                staff.full_name = staff.full_name.replace(" (Jurnalistika)", "")
                await session.commit()
                print(f"New Name: {staff.full_name}")
            else:
                print("Name already clean.")
        else:
            print(f"Staff with ID {staff_id} not found!")

if __name__ == "__main__":
    asyncio.run(run())

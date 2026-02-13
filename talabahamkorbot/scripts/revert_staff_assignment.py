
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff, StaffRole

async def run():
    async with AsyncSessionLocal() as session:
        staff_id = 80
        staff = await session.get(Staff, staff_id)
        
        if staff:
            print(f"Reverting Staff: {staff.full_name}")
            print(f"Current: Faculty={staff.faculty_id}, Role={staff.role}")
            
            # Revert to Jurnalistika (ID 36 based on previous search)
            staff.faculty_id = 36 
            staff.role = StaffRole.RAHBARIYAT
            staff.position = "Dekan" # Keeping position as 'Dekan' or whatever it was, likely 'Dekan'
            
            # Restore name format if needed
            if "(Jurnalistika)" not in staff.full_name:
                staff.full_name = f"{staff.full_name} (Jurnalistika)"
            
            await session.commit()
            print(f"Reverted: Faculty={staff.faculty_id}, Role={staff.role}, Name={staff.full_name}")
        else:
            print(f"Staff with ID {staff_id} not found!")

if __name__ == "__main__":
    asyncio.run(run())

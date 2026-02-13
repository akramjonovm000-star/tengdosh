
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff, Faculty, StaffRole
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as session:
        # 1. Get or Create Faculty
        target_name = "Axborot xizmati va jamoatchilik bilan aloqalar"
        stmt = select(Faculty).where(Faculty.name == target_name)
        faculty = (await session.execute(stmt)).scalar_one_or_none()
        
        if not faculty:
            print(f"Creating new Faculty: {target_name}")
            # Use faculty_code matching the model definition
            faculty = Faculty(name=target_name, university_id=1, faculty_code="AXBOROT")
            session.add(faculty)
            await session.commit()
            await session.refresh(faculty)
        else:
            print(f"Faculty found: {faculty.id}")
            
        # 2. Get Staff
        staff_id = 80
        staff = await session.get(Staff, staff_id)
        
        if staff:
            print(f"Updating Staff: {staff.full_name}")
            print(f"Old: Faculty={staff.faculty_id}, Role={staff.role}")
            
            staff.faculty_id = faculty.id
            staff.role = StaffRole.DEKAN
            staff.position = "Dekan" # Or 'Rahbar', but complying with user request 'dekan qilib qo'y'
            
            await session.commit()
            print(f"New: Faculty={staff.faculty_id}, Role={staff.role}")
        else:
            print(f"Staff with ID {staff_id} not found!")

if __name__ == "__main__":
    asyncio.run(run())

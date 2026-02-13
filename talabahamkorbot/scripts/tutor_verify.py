import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select, func
from database.models import Student, TutorGroup, Staff

async def verify():
    async with AsyncSessionLocal() as session:
        print("--- DATABASE STATISTICS ---")
        # 1. Total Counts
        s_count = await session.scalar(select(func.count(Student.id)))
        g_count = await session.scalar(select(func.count(TutorGroup.id)))
        t_count = await session.scalar(select(func.count(Staff.id)))
        
        print(f"Total Students: {s_count}")
        print(f"Total Tutor Groups: {g_count}")
        print(f"Total Staff: {t_count}")
        
        # 2. Check Specific Tutor
        tutor_names = ["TUGALOV SUHROBBEK XUDOYOR O‘G‘LI", "ERGASHOVA GULJAHON ABDULLAYEVNA"]
        
        for tutor_name in tutor_names:
            stmt = select(Staff).where(Staff.full_name.ilike(f"%{tutor_name}%"))
            tutor = (await session.execute(stmt)).scalar_one_or_none()
            
            if tutor:
                print(f"\n--- Verifying Tutor: {tutor.full_name} (ID: {tutor.id}) ---")
                
                # Get Groups
                groups = (await session.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor.id))).scalars().all()
                print(f"Assigned Groups ({len(groups)}): {[g.group_number for g in groups]}")
                
                # Get Students
                group_nums = [g.group_number for g in groups]
                if group_nums:
                    students = (await session.execute(select(Student).where(Student.group_number.in_(group_nums)))).scalars().all()
                    print(f"Total Students for Tutor: {len(students)}")
                    if students:
                        print("Sample Students:")
                        for s in students[:5]:
                            print(f" - {s.full_name} ({s.group_number}) [HemisID: {s.hemis_id}]")
            else:
                print(f"Tutor {tutor_name} not found.")

if __name__ == "__main__":
    asyncio.run(verify())

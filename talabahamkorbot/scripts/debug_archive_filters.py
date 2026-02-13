import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from config import DATABASE_URL
from database.models import Staff, Student, StaffRole
from api.management import build_student_filter

async def debug_filters():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check Staff 27
        staff = await session.get(Staff, 27)
        if not staff:
            print("Staff 27 not found!")
            return

        print(f"--- Staff 27 Info ---")
        print(f"ID: {staff.id}")
        print(f"Role: {staff.role} (Type: {type(staff.role)})")
        print(f"University ID: {staff.university_id}")
        
        staff_role = staff.role
        global_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
        
        # Manually check is_global as in management.py
        is_global = getattr(staff, 'hemis_role', None) == 'rahbariyat' or staff_role in global_roles
        print(f"Is Global: {is_global}")
        print(f"Staff Role in Global Roles: {staff_role in global_roles}")
        print(f"Global Roles: {[r.value for r in global_roles]}")
        
        # Check what filters are generated
        filters = build_student_filter(staff)
        print(f"\nGenerated Filters: {filters}")
        
        # Check if any students match these filters
        from sqlalchemy import and_
        stmt = select(Student).where(and_(*filters)).limit(5)
        res = await session.execute(stmt)
        students = res.scalars().all()
        print(f"Matching Students (Sample): {[s.full_name for s in students]}")
        
        count_stmt = select(Student.id).where(and_(*filters))
        count_res = await session.execute(count_stmt)
        results = count_res.all()
        total_count = len(results)
        print(f"Total Matching Students: {total_count}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_filters())

import asyncio
import re
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as s:
        # Check Students
        res = await s.execute(select(Student.full_name))
        students = res.scalars().all()
        s_initials = [n for n in students if re.search(r'\b[A-Z]\.', n)]
        
        # Check Staff
        res = await s.execute(select(Staff.full_name))
        staff = res.scalars().all()
        f_initials = [n for n in staff if re.search(r'\b[A-Z]\.', n)]
        
        print(f'Students with initials: {len(s_initials)} / {len(students)}')
        if s_initials:
            print(f'Sample Student initials: {s_initials[:5]}')
            
        print(f'Staff with initials: {len(f_initials)} / {len(staff)}')
        if f_initials:
            print(f'Sample Staff initials: {f_initials[:5]}')

if __name__ == "__main__":
    asyncio.run(run())

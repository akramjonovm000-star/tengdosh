import asyncio
import re
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as s:
        # PostgreSQL Regex: ~
        # But we can also just fetch all group numbers and check locally
        res = await s.execute(select(Student.full_name, Student.group_number))
        rows = res.all()
        
        groups_to_fix = set()
        for full_name, group_number in rows:
            if re.search(r'\b[A-Z]\.', full_name):
                if group_number:
                    groups_to_fix.add(group_number)
        
        print(f'Total groups with initials: {len(groups_to_fix)}')
        # Print first 5 groups
        print(f'Sample groups: {list(groups_to_fix)[:5]}')

if __name__ == "__main__":
    asyncio.run(run())

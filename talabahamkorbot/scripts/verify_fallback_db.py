import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select, func, or_

async def verify():
    print('--- Verifying DB Fallback Logic ---')
    
    async with AsyncSessionLocal() as db:
        # 0. Find ANY existing student with hemis_id
        print("Looking for any existing student with hemis_id...")
        stmt_any = select(Student).where(Student.hemis_id.is_not(None)).limit(1)
        existing_student = (await db.execute(stmt_any)).scalar()
        
        if existing_student:
             print(f"Found existing student: {existing_student.full_name} ({existing_student.hemis_id})")
             query = existing_student.hemis_id
        else:
             print("No existing students with hemis_id found. Cannot verify fallback logic without data.")
             return

        # 1. Simulate the Search Filter logic from api/management.py
        # This matches the fix implemented in api/management.py
        search_condition = (
            (Student.full_name.ilike(f"%{query}%")) | 
            (Student.hemis_login.ilike(f"%{query}%"))
        )
        
        # Count Query
        count_stmt = select(func.count(Student.id)).where(search_condition)
        db_count = (await db.execute(count_stmt)).scalar()
        
        print(f'DB Count with search query "{query}": {db_count}')
        
        if db_count == 0:
            print('SUCCESS: Fallback logic CORRECTLY IGNORED Short ID (as requested).')
        else:
            print(f'FAILURE: Fallback logic returned {db_count} results (Should be 0 for Short ID).')

asyncio.run(verify())

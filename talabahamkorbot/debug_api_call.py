import asyncio
import sys
import os
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select
from api.tutor import get_group_appeals

async def debug_call():
    async with AsyncSessionLocal() as db:
        # 1. Mock Tutor
        tutor = (await db.execute(select(Staff).where(Staff.jshshir == '12345678901234'))).scalar()
        if not tutor:
            print("ERROR: Tutor not found")
            return

        print(f"Simulating request for Tutor: {tutor.id} ({tutor.full_name}) Group: DEMO-305")
        
        try:
            # 2. Call Function
            response = await get_group_appeals(
                group_number="DEMO-305",
                status=None,
                db=db,
                tutor=tutor
            )
            
            print(f"Success: {response['success']}")
            data = response['data']
            print(f"Count: {len(data)}")
            for item in data:
                print(f" - {item['student_name']}: {item['text'][:30]}... (File: {item.get('file_id')}) (Fac: {item.get('student_faculty')})")
                
        except Exception as e:
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_call())

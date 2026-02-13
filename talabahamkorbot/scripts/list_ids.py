
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff

async def list_samples():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Student.hemis_id, Student.full_name).limit(5))
        print('Student Sample HEMIS IDs:')
        for r in res.all():
            print(f"  - {r.hemis_id}: {r.full_name}")
            
        res = await s.execute(select(Staff.hemis_id, Staff.full_name).limit(5))
        print('Staff Sample HEMIS IDs:')
        for r in res.all():
            print(f"  - {r.hemis_id}: {r.full_name}")

if __name__ == "__main__":
    asyncio.run(list_samples())

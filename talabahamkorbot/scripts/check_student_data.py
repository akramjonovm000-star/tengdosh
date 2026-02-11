import asyncio
import sys
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(Student).where(Student.hemis_id.isnot(None)).limit(10)
        result = await db.execute(stmt)
        students = result.scalars().all()
        for s in students:
            print(f"Name: {s.full_name}")
            print(f"  HemisID: {s.hemis_id}")
            print(f"  Login:   {s.hemis_login}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())

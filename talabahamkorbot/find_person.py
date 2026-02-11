import asyncio
import sys
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(Student).where(Student.hemis_login == '395251101397')
        result = await db.execute(stmt)
        s = result.scalar_one_or_none()
        if s:
            print(f"ID: {s.id}")
            print(f"Name: {s.full_name}")
            print(f"HemisID: {s.hemis_id}")
            print(f"Login: {s.hemis_login}")
        else:
            print("Not found")

if __name__ == "__main__":
    asyncio.run(main())

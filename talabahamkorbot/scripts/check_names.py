import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as s:
        # Check specific names and overall stats
        res = await s.execute(select(Student.id, Student.full_name, Student.hemis_login).order_by(Student.id.desc()).limit(10))
        for row in res:
            print(f"ID: {row.id}, Name: '{row.full_name}', Login: {row.hemis_login}")
        
        talabas = await s.execute(select(Student.id).where(Student.full_name == 'Talaba'))
        print(f"Total 'Talaba' names: {len(talabas.all())}")

if __name__ == '__main__':
    asyncio.run(check())

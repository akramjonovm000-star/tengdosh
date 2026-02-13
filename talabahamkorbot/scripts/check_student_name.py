import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Student).where(Student.hemis_id == '8286'))
        row = res.scalar_one_or_none()
        if row:
            print(f'Student Name: {row.full_name}, Short: {row.short_name}')
        else:
            print('Student not found')

if __name__ == "__main__":
    asyncio.run(run())

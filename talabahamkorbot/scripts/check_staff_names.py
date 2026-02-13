import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Staff).where(Staff.id == 27))
        row = res.scalar_one_or_none()
        if row:
            print(f'Staff Name: {row.full_name}, Short: {row.short_name}, Role: {row.role}')
        else:
            print('Staff not found')

if __name__ == "__main__":
    asyncio.run(run())

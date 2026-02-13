import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Staff))
        rows = res.scalars().all()
        for r in rows:
            print(f'Staff ID: {r.id}, Name: {r.full_name}, HEMIS ID: {r.hemis_id}')

if __name__ == "__main__":
    asyncio.run(run())

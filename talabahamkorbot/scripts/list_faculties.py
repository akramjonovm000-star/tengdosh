
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Faculty
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as session:
        print("Listing Faculties...")
        stmt = select(Faculty)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        
        for f in rows:
            print(f"ID: {f.id}, Name: '{f.name}'")

if __name__ == "__main__":
    asyncio.run(run())

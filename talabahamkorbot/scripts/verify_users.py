import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select, func
from database.db_connect import engine, Base
from database.models import User

async def verify():
    async with engine.begin() as conn:
        # Check count
        # We need session
        pass
    
    from database.db_connect import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        print(f"Total Users: {count}")
        
        # Show first 5
        result = await session.execute(select(User).limit(5))
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.id} | Login: {u.hemis_login} | Name: {u.full_name} | Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(verify())

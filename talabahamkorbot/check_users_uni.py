import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import User

async def check():
    async with AsyncSessionLocal() as db:
        users_count = await db.scalar(select(func.count(User.id)).where(User.university_id == 1))
        
        print(f"Total rows in 'users' table for JMCU: {users_count}")
        
        users_count_other = await db.scalar(select(func.count(User.id)).where(User.university_id != 1))
        print(f"Total rows in 'users' table for others: {users_count_other}")
        
        count_all = await db.scalar(select(func.count(User.id)))
        print(f"Total globally: {count_all}")

if __name__ == '__main__':
    asyncio.run(check())

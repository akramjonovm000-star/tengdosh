import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaComment

async def check():
    async with AsyncSessionLocal() as db:
        q = select(func.count()).select_from(ChoyxonaComment).where(ChoyxonaComment.created_at == None)
        count = await db.scalar(q)
        print(f"NULL created_at count: {count}")

if __name__ == '__main__':
    asyncio.run(check())

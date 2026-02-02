import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaComment

async def check():
    async with AsyncSessionLocal() as db:
        q = select(func.count()).select_from(ChoyxonaComment).where(ChoyxonaComment.likes_count == None)
        count = await db.scalar(q)
        print(f"NULL likes count: {count}")
        
        if count > 0:
            print("Fixing NULL likes...")
            from sqlalchemy import update
            await db.execute(update(ChoyxonaComment).where(ChoyxonaComment.likes_count == None).values(likes_count=0))
            await db.commit()
            print("Fixed.")

if __name__ == '__main__':
    asyncio.run(check())

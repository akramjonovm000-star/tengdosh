
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal as async_session_maker
from sqlalchemy import select, desc
from database.models import Banner

async def check():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Banner).order_by(desc(Banner.id)).limit(10)
        )
        banners = result.scalars().all()
        print(f"Total banners found: {len(banners)}")
        for b in banners:
            print(f"ID: {b.id}, Active: {b.is_active}, FileID: {b.image_file_id}, Link: {b.link}")

if __name__ == "__main__":
    asyncio.run(check())

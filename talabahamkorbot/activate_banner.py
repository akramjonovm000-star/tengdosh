
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select, update, desc
from database.models import Banner

async def activate():
    async with AsyncSessionLocal() as session:
        # Get latest
        result = await session.execute(select(Banner).order_by(desc(Banner.id)).limit(1))
        banner = result.scalar_one_or_none()
        
        if banner:
            print(f"Activating banner {banner.id}...")
            # Deactivate others
            await session.execute(update(Banner).where(Banner.id != banner.id).values(is_active=False))
            # Activate this one
            banner.is_active = True
            await session.commit()
            print("Done.")
        else:
            print("No banners found.")

if __name__ == "__main__":
    asyncio.run(activate())

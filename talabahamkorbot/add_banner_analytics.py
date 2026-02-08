
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import text

async def upgrade():
    async with AsyncSessionLocal() as session:
        print("Adding views and clicks columns to banners table...")
        try:
            await session.execute(text("ALTER TABLE banners ADD COLUMN views INTEGER DEFAULT 0"))
            print("Added views column.")
        except Exception as e:
            print(f"Error adding views column (might exist): {e}")
            
        try:
            await session.execute(text("ALTER TABLE banners ADD COLUMN clicks INTEGER DEFAULT 0"))
            print("Added clicks column.")
        except Exception as e:
            print(f"Error adding clicks column (might exist): {e}")
            
        await session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(upgrade())

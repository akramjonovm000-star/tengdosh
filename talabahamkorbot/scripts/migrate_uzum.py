import asyncio
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import engine

async def migrate():
    print("Migrating transactions table for Uzum...")
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS uzum_trans_id VARCHAR(64);"))
    print("Done!")

if __name__ == "__main__":
    asyncio.run(migrate())

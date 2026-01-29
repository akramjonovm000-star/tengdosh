
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from database.db_connect import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            print("Adding target_hemis_id column to student_feedback table...")
            await conn.execute(text("ALTER TABLE student_feedback ADD COLUMN target_hemis_id BIGINT;"))
            print("Done.")
        except Exception as e:
            if "duplicate column" in str(e):
                print("Column already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

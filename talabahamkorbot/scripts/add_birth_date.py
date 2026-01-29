
import asyncio
import sys
import os
from sqlalchemy import text

# Add parent dir to path to import database/config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import engine

async def migrate():
    print("Starting migration...")
    async with engine.begin() as conn:
        try:
            # Check if column exists first (optional but safe) or just try adding
            # Postgres doesn't support "IF NOT EXISTS" in ADD COLUMN standardly in older versions, 
            # but usually "ADD COLUMN IF NOT EXISTS" works in newer PG.
            # Let's try simple ADD COLUMN and catch exception.
            
            await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS birth_date VARCHAR(32);"))
            print("Migration successful: Added birth_date column.")
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

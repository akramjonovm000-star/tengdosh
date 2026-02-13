import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from config import DATABASE_URL

async def fix_schema():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print(f"--- Fixing Pending Uploads Schema ---")
        
        try:
            print("Adding file_unique_id column...")
            await conn.execute(text("ALTER TABLE pending_uploads ADD COLUMN IF NOT EXISTS file_unique_id VARCHAR(128);"))
        except Exception as e:
            print(f"Error adding file_unique_id: {e}")

        try:
            print("Adding file_size column...")
            await conn.execute(text("ALTER TABLE pending_uploads ADD COLUMN IF NOT EXISTS file_size BIGINT;"))
        except Exception as e:
            print(f"Error adding file_size: {e}")

        try:
            print("Adding mime_type column...")
            await conn.execute(text("ALTER TABLE pending_uploads ADD COLUMN IF NOT EXISTS mime_type VARCHAR(128);"))
        except Exception as e:
            print(f"Error adding mime_type: {e}")
            
        print("Schema update completed.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_schema())

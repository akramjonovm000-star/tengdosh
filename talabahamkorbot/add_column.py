
import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def add_column():
    async with AsyncSessionLocal() as session:
        try:
            print("Attempting to add column hemis_token to staff table...")
            await session.execute(text("ALTER TABLE staff ADD COLUMN hemis_token VARCHAR(1024);"))
            await session.commit()
            print("Column added successfully.")
        except Exception as e:
            print(f"Error (possibly column exists): {e}")

if __name__ == "__main__":
    import sys
    import os
    # Ensure current directory is in path for imports
    sys.path.append(os.getcwd())
    asyncio.run(add_column())

import asyncio
import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        # Create table for caching Telegram File IDs
        sql = """
        CREATE TABLE IF NOT EXISTS resource_files (
            id SERIAL PRIMARY KEY,
            hemis_id INTEGER UNIQUE NOT NULL,
            file_id VARCHAR(255) NOT NULL,
            file_name VARCHAR(255),
            file_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        try:
            await session.execute(text(sql))
            await session.commit()
            print("Table 'resource_files' created successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    asyncio.run(main())

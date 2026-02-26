import asyncio
import sys
import os

# Add parent directory to path to allow imports from database and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import engine
from database.models import Base

async def main():
    print("Creating new club tables...")
    async with engine.begin() as conn:
        # Add new model tables to the database
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())

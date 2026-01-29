import asyncio
from database.db_connect import engine
from database.models import Base

async def create_market_table():
    async with engine.begin() as conn:
        print("Adding market_items table...")
        await conn.run_sync(Base.metadata.create_all)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(create_market_table())

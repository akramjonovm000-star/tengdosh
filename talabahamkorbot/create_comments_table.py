
import asyncio
from database.db_connect import engine
from database.models import Base

async def create_tables():
    print("Creating missing tables (ChoyxonaComment)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(create_tables())

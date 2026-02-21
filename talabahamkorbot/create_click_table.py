import asyncio
from database.db_connect import engine
from database.models import Base

async def init_table():
    async with engine.begin() as conn:
        from database.models import ClickTransaction
        await conn.run_sync(Base.metadata.create_all)
        print("ClickTransaction table created or verified.")

if __name__ == "__main__":
    asyncio.run(init_table())

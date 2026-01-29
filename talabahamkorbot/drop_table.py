import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def drop_pending():
    async with engine.begin() as conn:
        print("Dropping pending_uploads table...")
        await conn.execute(text("DROP TABLE IF EXISTS pending_uploads CASCADE"))
        print("Dropped.")

if __name__ == "__main__":
    asyncio.run(drop_pending())

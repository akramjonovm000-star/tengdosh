import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"))
        tables = result.scalars().all()
        print("--- Tables in DB ---")
        for t in tables:
            print(t)

if __name__ == "__main__":
    asyncio.run(main())

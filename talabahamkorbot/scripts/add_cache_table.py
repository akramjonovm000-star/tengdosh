import asyncio
from database.db_connect import engine, Base
from database.models import StudentCache # Import to register

async def main():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

if __name__ == "__main__":
    asyncio.run(main())

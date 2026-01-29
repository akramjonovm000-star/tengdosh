import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

async def add_column():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            print("Adding hemis_login column to staff table...")
            await conn.execute(text("ALTER TABLE staff ADD COLUMN hemis_login VARCHAR(128);"))
            await conn.execute(text("CREATE UNIQUE INDEX uq_staff_hemis_login ON staff (hemis_login);"))
            print("Success!")
        except Exception as e:
            print(f"Error (maybe already exists): {e}")

if __name__ == "__main__":
    asyncio.run(add_column())

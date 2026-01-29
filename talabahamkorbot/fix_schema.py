import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def fix_schema():
    async with AsyncSessionLocal() as session:
        print("🛠️ Applying Schema Fix: Increasing group_number length...")
        await session.execute(text("ALTER TABLE students ALTER COLUMN group_number TYPE VARCHAR(255)"))
        await session.commit()
        print("✅ Schema fixed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_schema())

import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def migrate_specialty():
    async with AsyncSessionLocal() as session:
        print("🛠️ Adding Specialty Column...")
        try:
            await session.execute(text("ALTER TABLE students ADD COLUMN specialty_name VARCHAR(255)"))
            print("✅ Added specialty_name")
        except Exception as e:
            print(f"⚠️ specialty_name exists or error: {e}")
            
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(migrate_specialty())

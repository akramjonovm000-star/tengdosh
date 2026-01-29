import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def migrate_profile_fields():
    async with AsyncSessionLocal() as session:
        print("🛠️ Adding Profile Fields (university_name, faculty_name)...")
        try:
            await session.execute(text("ALTER TABLE students ADD COLUMN university_name VARCHAR(255)"))
            print("✅ Added university_name")
        except Exception as e:
            print(f"⚠️ university_name exists or error: {e}")

        try:
            await session.execute(text("ALTER TABLE students ADD COLUMN faculty_name VARCHAR(255)"))
            print("✅ Added faculty_name")
        except Exception as e:
            print(f"⚠️ faculty_name exists or error: {e}")
            
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(migrate_profile_fields())

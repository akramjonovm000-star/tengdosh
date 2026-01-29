import asyncio
from database.db_connect import engine
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        print("Checking for hemis_role column...")
        try:
            # Check if column exists, if not add it
            await conn.execute(text("ALTER TABLE students ADD COLUMN hemis_role VARCHAR(50)"))
            print("Added hemis_role column.")
        except Exception as e:
            if "duplicate" in str(e).lower() or "exists" in str(e).lower():
                print("Column hemis_role already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def add_username_column():
    async with AsyncSessionLocal() as session:
        try:
            print("Checking if username column exists...")
            # Simple check by selecting (will fail if not exists) - or better, just try adding and ignore error
            # But "ADD COLUMN IF NOT EXISTS" is specific to some DBs. Postgres supports it.
            # SQLite doesn't directly support IF NOT EXISTS in ADD COLUMN in older versions, but let's try standard ALTER.
            
            # Since we are using Postgres (likely given asyncpg/psycopg usage in typical fastapi apps, though user env is ambiguouos, let's assume Postgres or robust SQL)
            # Actually, previous interactions suggested SQL.
            
            await session.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS username VARCHAR(50);"))
            await session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_students_username ON students (username);"))
            
            await session.commit()
            print("✅ Username column added successfully.")
        except Exception as e:
            print(f"⚠️ Error (might already exist): {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_username_column())

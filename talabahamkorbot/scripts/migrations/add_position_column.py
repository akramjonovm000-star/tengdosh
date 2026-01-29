import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def add_position_column():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE staff ADD COLUMN position VARCHAR(255);"))
            print("✅ 'position' column added successfully.")
        except Exception as e:
            print(f"⚠️ Column might already exist or error: {e}")

if __name__ == "__main__":
    asyncio.run(add_position_column())

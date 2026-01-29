import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def add_limit_column():
    async with engine.begin() as conn:
        # ai_limit
        await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS ai_limit INTEGER DEFAULT 25"))
        print("✅ Added ai_limit column")

if __name__ == "__main__":
    asyncio.run(add_limit_column())

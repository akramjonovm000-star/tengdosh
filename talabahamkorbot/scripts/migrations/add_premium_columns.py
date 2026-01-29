import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def add_premium_columns():
    async with engine.begin() as conn:
        # ai_usage_count
        await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS ai_usage_count INTEGER DEFAULT 0"))
        # ai_last_reset
        await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS ai_last_reset TIMESTAMP"))
        # custom_badge
        await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS custom_badge VARCHAR(32)"))

        print("✅ Added premium columns to students table")

if __name__ == "__main__":
    asyncio.run(add_premium_columns())

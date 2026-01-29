
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def add_ai_columns():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN ai_context TEXT;"))
            print("Added ai_context")
        except Exception as e:
            print(f"ai_context error (maybe exists): {e}")

        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN last_context_update TIMESTAMP;"))
            print("Added last_context_update")
        except Exception as e:
            print(f"last_context_update error (maybe exists): {e}")

if __name__ == "__main__":
    asyncio.run(add_ai_columns())

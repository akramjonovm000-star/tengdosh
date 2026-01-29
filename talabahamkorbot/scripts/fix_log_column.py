
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def alter_table():
    async with engine.begin() as conn:
        try:
            # PostgreSQL syntax to alter column type
            await conn.execute(text("ALTER TABLE student_ai_logs ALTER COLUMN group_number TYPE VARCHAR(255);"))
            print("Successfully altered group_number to VARCHAR(255)")
        except Exception as e:
            print(f"Error altering table: {e}")

if __name__ == "__main__":
    asyncio.run(alter_table())

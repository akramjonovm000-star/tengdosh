import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def alter_table():
    async with engine.begin() as conn:
        print("Altering tyutor_work_log table...")
        try:
            # PostgreSQL specific syntax to drop NOT NULL
            await conn.execute(text("ALTER TABLE tyutor_work_log ALTER COLUMN student_id DROP NOT NULL"))
            print("Successfully dropped NOT NULL constraint from student_id")
        except Exception as e:
            print(f"Error altering table: {e}")

if __name__ == "__main__":
    asyncio.run(alter_table())

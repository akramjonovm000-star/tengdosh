import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def add_columns():
    async with engine.begin() as conn:
        print("Checking/Adding 'title' column...")
        try:
            await conn.execute(text("ALTER TABLE tyutor_work_log ADD COLUMN title VARCHAR(255)"))
            print("Added 'title'")
        except Exception as e:
            print(f"'title' column might already exist: {e}")

        print("Checking/Adding 'completion_date' column...")
        try:
            await conn.execute(text("ALTER TABLE tyutor_work_log ADD COLUMN completion_date VARCHAR(20)"))
            print("Added 'completion_date'")
        except Exception as e:
            print(f"'completion_date' column might already exist: {e}")

if __name__ == "__main__":
    asyncio.run(add_columns())

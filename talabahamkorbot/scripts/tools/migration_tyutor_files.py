import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def migrate_tyutor_log():
    async with engine.begin() as conn:
        print("Adding file_id and file_type to tyutor_work_log...")
        
        # Add file_id
        try:
            await conn.execute(text("ALTER TABLE tyutor_work_log ADD COLUMN file_id VARCHAR(255) DEFAULT NULL;"))
            print("Added file_id column.")
        except Exception as e:
            print(f"Skipping file_id (maybe exists): {e}")

        # Add file_type
        try:
            await conn.execute(text("ALTER TABLE tyutor_work_log ADD COLUMN file_type VARCHAR(32) DEFAULT NULL;"))
            print("Added file_type column.")
        except Exception as e:
            print(f"Skipping file_type (maybe exists): {e}")

if __name__ == "__main__":
    asyncio.run(migrate_tyutor_log())

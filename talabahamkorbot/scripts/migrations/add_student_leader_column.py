
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from database.db_connect import engine

async def upgrade():
    async with engine.begin() as conn:
        print("Adding leader_student_id column to clubs table...")
        try:
            await conn.execute(text("ALTER TABLE clubs ADD COLUMN leader_student_id INTEGER REFERENCES students(id) ON DELETE SET NULL"))
            print("Column added successfully.")
        except Exception as e:
            print(f"Error (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(upgrade())

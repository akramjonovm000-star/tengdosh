
import asyncio
from database.db_connect import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name, character_maximum_length FROM information_schema.columns WHERE table_name = 'student_feedback' AND column_name IN ('student_group', 'student_faculty', 'student_full_name');"))
        for row in res:
            print(f"Column: {row[0]} | MaxLen: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check())

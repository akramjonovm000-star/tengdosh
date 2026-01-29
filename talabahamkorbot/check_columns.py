
import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def get_columns():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'student_feedback'"))
        for row in res:
            print(f"Column: {row[0]} | Type: {row[1]} | Length: {row[2]}")

if __name__ == "__main__":
    asyncio.run(get_columns())

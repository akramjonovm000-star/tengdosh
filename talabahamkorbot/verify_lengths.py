
import asyncio
from database.db_connect import engine
from sqlalchemy import text

async def c():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name, character_maximum_length FROM information_schema.columns WHERE table_name = 'student_feedback' AND column_name IN ('ai_topic', 'assigned_role')"))
        for r in res: print(f'Col: {r[0]} | Len: {r[1]}')
if __name__ == "__main__":
    asyncio.run(c())

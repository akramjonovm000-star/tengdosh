
import asyncio
from database.db_connect import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        print("--- Triggers ---")
        res = await conn.execute(text("SELECT tgname, event_object_table FROM information_schema.triggers"))
        for r in res: print(f'Trigger: {r[0]} | Table: {r[1]}')
        
        print("\n--- 64 length columns ---")
        res = await conn.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE character_maximum_length = 64"))
        for r in res: print(f'Table: {r[0]} | Col: {r[1]}')
        
        print("\n--- All columns for student_feedback ---")
        res = await conn.execute(text("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'student_feedback'"))
        for r in res: print(f'Col: {r[0]} | Type: {r[1]} | Len: {r[2]}')

if __name__ == "__main__":
    asyncio.run(check())

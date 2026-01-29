import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            # Check if column exists
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='students' AND column_name='hemis_password'"))
            if not result.fetchone():
                print("Adding hemis_password column...")
                await conn.execute(text("ALTER TABLE students ADD COLUMN hemis_password VARCHAR(255)"))
                print("Column added successfully.")
            else:
                print("Column hemis_password already exists.")
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == '__main__':
    asyncio.run(migrate())

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import DATABASE_URL

async def migrate():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        try:
            # Check if column exists
            query = text("SELECT column_name FROM information_schema.columns WHERE table_name='rating_records' AND column_name='answers';")
            result = await conn.execute(query)
            if not result.fetchone():
                print("Adding 'answers' column to 'rating_records'...")
                await conn.execute(text("ALTER TABLE rating_records ADD COLUMN answers JSONB DEFAULT '[]'::jsonb;"))
                print("Column added successfully.")
            else:
                print("Column 'answers' already exists.")
        except Exception as e:
            print(f"Error during migration: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())

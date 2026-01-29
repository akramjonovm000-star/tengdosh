import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def migrate():
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        print("Checking/Adding reply_to_comment_id to choyxona_comments...")
        try:
            await conn.execute(text("ALTER TABLE choyxona_comments ADD COLUMN IF NOT EXISTS reply_to_comment_id INTEGER REFERENCES choyxona_comments(id) ON DELETE SET NULL"))
            print("Successfully added reply_to_comment_id")
        except Exception as e:
            print(f"Error adding reply_to_comment_id: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

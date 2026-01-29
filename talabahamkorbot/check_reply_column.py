import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def check():
    async with engine.connect() as conn:
        print("Checking columns in choyxona_comments...")
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'choyxona_comments'"))
        columns = [row[0] for row in result.fetchall()]
        print(f"Columns: {columns}")
        
        if 'reply_to_comment_id' in columns:
            print("✅ reply_to_comment_id EXISTS")
        else:
            print("❌ reply_to_comment_id MISSING")

if __name__ == "__main__":
    asyncio.run(check())

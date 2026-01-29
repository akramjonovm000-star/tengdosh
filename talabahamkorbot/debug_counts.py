import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def count_content():
    async with engine.connect() as conn:
        print("Checking content counts...")
        
        posts = await conn.scalar(text("SELECT count(*) FROM choyxona_posts"))
        comments = await conn.scalar(text("SELECT count(*) FROM choyxona_comments"))
        
        print(f"Posts: {posts}")
        print(f"Comments: {comments}")

if __name__ == "__main__":
    asyncio.run(count_content())

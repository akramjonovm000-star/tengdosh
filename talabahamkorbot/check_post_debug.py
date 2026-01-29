import asyncio
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost

async def check_latest_post():
    async with AsyncSessionLocal() as db:
        print("Checking latest post...")
        result = await db.execute(
            select(ChoyxonaPost)
            .options(selectinload(ChoyxonaPost.likes))
            .order_by(desc(ChoyxonaPost.created_at))
            .limit(1)
        )
        post = result.scalar_one_or_none()
        
        if post:
            print(f"Post ID: {post.id}")
            print(f"Content: {post.content}")
            print(f"Author ID: {post.student_id}")
            print(f"Likes Count (Column): {post.likes_count}")
            print(f"Actual Likes (Table): {len(post.likes)}")
            print(f"Like Entries: {post.likes}")
        else:
            print("No posts found.")

if __name__ == "__main__":
    asyncio.run(check_latest_post())

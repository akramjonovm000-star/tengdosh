import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, update
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment

async def fix_counts():
    async with AsyncSessionLocal() as session:
        print("Fixing comment counts for all posts...")
        
        # Get all posts
        stmt = select(ChoyxonaPost)
        result = await session.execute(stmt)
        posts = result.scalars().all()
        
        for post in posts:
            # Count actual comments
            c_stmt = select(func.count()).select_from(ChoyxonaComment).where(ChoyxonaComment.post_id == post.id)
            actual_count = await session.scalar(c_stmt)
            
            if post.comments_count != actual_count:
                print(f"Post {post.id}: Updating count from {post.comments_count} to {actual_count}")
                post.comments_count = actual_count
        
        await session.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_counts())

import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment

async def check_post_comments():
    async with AsyncSessionLocal() as db:
        # Find the post
        result = await db.execute(select(ChoyxonaPost).where(ChoyxonaPost.content.ilike("%dalbayop antigravity%")))
        post = result.scalar_one_or_none()
        
        if not post:
            print("❌ Post not found!")
            return

        print(f"✅ Found Post ID: {post.id}")
        print(f"📄 Post Content: {post.content}")
        print(f"🔢 Stored comments_count: {post.comments_count}")
        
        # Count actual comments
        result = await db.execute(select(func.count()).select_from(ChoyxonaComment).where(ChoyxonaComment.post_id == post.id))
        actual_count = result.scalar()
        
        print(f"🔍 Actual Comment Rows: {actual_count}")
        
        if post.comments_count != actual_count:
            print("⚠️ MISMATCH DETECTED!")
            print("Fixing...")
            post.comments_count = actual_count
            await db.commit()
            print(f"✅ Fixed comments_count to {actual_count}")
        else:
            print("✅ Counts match locally.")

if __name__ == "__main__":
    asyncio.run(check_post_comments())

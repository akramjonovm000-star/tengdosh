import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment

async def check_comments():
    async with AsyncSessionLocal() as db:
        # 1. Find Post
        result = await db.execute(select(ChoyxonaPost).where(ChoyxonaPost.content.ilike("%Bugun lookda%")))
        post = result.scalars().first()
        
        if not post:
            print("Post not found!")
            return

        print(f"Post ID: {post.id} | Content: {post.content[:50]}...")
        
        # 2. Get All Comments
        result = await db.execute(select(ChoyxonaComment).where(ChoyxonaComment.post_id == post.id).order_by(ChoyxonaComment.created_at))
        comments = result.scalars().all()
        
        print(f"\nTotal Comments: {len(comments)}")
        
        comment_map = {c.id: c for c in comments}
        
        for c in comments:
            parent_info = "ROOT"
            if c.reply_to_comment_id:
                parent = comment_map.get(c.reply_to_comment_id)
                parent_info = f"-> Reply to {c.reply_to_comment_id} ({parent.content[:20] if parent else 'MISSING'})"
            
            print(f"ID: {c.id} | Author: {c.student_id} | Content: '{c.content}' | {parent_info}")

        # Check for 'what up' globally in case it was saved to wrong post
        result = await db.execute(select(ChoyxonaComment).where(ChoyxonaComment.content == "what up"))
        orphans = result.scalars().all()
        if orphans:
            print("\n--- Searching for 'what up' globally ---")
            for c in orphans:
                print(f"ID: {c.id} | Post ID: {c.post_id} | ReplyTo: {c.reply_to_comment_id}")

if __name__ == "__main__":
    asyncio.run(check_comments())

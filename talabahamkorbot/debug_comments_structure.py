import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select, desc
from database.models import ChoyxonaComment, ChoyxonaPost

async def check_comments():
    async with AsyncSessionLocal() as db:
        # Get latest post with comments
        idx = 0
        posts = (await db.execute(select(ChoyxonaPost).order_by(desc(ChoyxonaPost.created_at)).limit(5))).scalars().all()
        
        target_post = None
        for p in posts:
            count = await db.scalar(select(ChoyxonaComment.id).where(ChoyxonaComment.post_id == p.id).limit(1))
            if count:
                target_post = p
                break
        
        if not target_post:
            print("No posts with comments found.")
            return

        print(f"Checking Comments for Post {target_post.id} (Content: {target_post.content[:20]}...)")
        
        comments = (await db.execute(select(ChoyxonaComment).where(ChoyxonaComment.post_id == target_post.id))).scalars().all()
        
        print(f"{'ID':<5} | {'Content':<20} | {'ReplyToID':<10} | {'ReplyToUser':<15} | {'CreatedAt'}")
        print("-" * 80)
        for c in comments:
            print(f"{c.id:<5} | {c.content[:20]:<20} | {str(c.reply_to_comment_id):<10} | {str(c.reply_to_user_id):<15} | {c.created_at}")

        # Check raw serialization simulation
        from api.community import _map_comment
        # We need a dummy student author for mapping? No, mapping uses c.student
        # We need to eager load for mapping to work fully, but let's just inspect the fields.
        
if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_comments())

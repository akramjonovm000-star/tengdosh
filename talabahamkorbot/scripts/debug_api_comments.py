import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaComment, Student

async def debug_get_comments(post_id: int):
    async with AsyncSessionLocal() as db:
        try:
            print(f"Fetching post {post_id}...")
            post = await db.get(ChoyxonaPost, post_id)
            if not post:
                print("Post not found")
                return

            print("Fetching comments with eager loading...")
            query = select(ChoyxonaComment).options(
                selectinload(ChoyxonaComment.student),
                selectinload(ChoyxonaComment.parent_comment).selectinload(ChoyxonaComment.student),
                selectinload(ChoyxonaComment.reply_to_user),
                selectinload(ChoyxonaComment.likes),
                selectinload(ChoyxonaComment.post)
            ).where(ChoyxonaComment.post_id == post_id)
            
            result = await db.execute(query)
            all_comments = result.scalars().all()
            print(f"Found {len(all_comments)} comments")
            
            print("Sorting comments...")
            all_comments.sort(key=lambda x: (-(x.likes_count or 0), x.created_at))
            print("Sorted successfully")
            
            from api.community import _map_comment
            print("Mapping comments...")
            mapped = [_map_comment(c, c.student, 730) for c in all_comments]
            print(f"Mapped {len(mapped)} comments successfully")
            
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_get_comments(40))

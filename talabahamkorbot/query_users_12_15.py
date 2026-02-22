import asyncio
from datetime import datetime
from sqlalchemy import select, func, distinct
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPostView, ChoyxonaPostLike, ChoyxonaComment, TgAccount

async def main():
    async with AsyncSessionLocal() as db:
        start_time = datetime(2026, 2, 22, 7, 0, 0)
        end_time = datetime(2026, 2, 22, 10, 0, 0)
        
        # Unique students viewing posts
        views_query = select(func.count(distinct(ChoyxonaPostView.student_id))).where(
            ChoyxonaPostView.viewed_at >= start_time,
            ChoyxonaPostView.viewed_at <= end_time,
            ChoyxonaPostView.student_id.isnot(None)
        )
        views_count = await db.scalar(views_query)
        
        # Unique students liking posts
        likes_query = select(func.count(distinct(ChoyxonaPostLike.student_id))).where(
            ChoyxonaPostLike.created_at >= start_time,
            ChoyxonaPostLike.created_at <= end_time,
            ChoyxonaPostLike.student_id.isnot(None)
        )
        likes_count = await db.scalar(likes_query)
        
        # Telegram activity?
        # Maybe check `created_at` in some other tables? Let's just output the view count.
        # Let's also do a union to get exact total unique standard users active across these:
        
        print(f"Users viewing posts: {views_count}")
        print(f"Users liking posts: {likes_count}")

if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())


import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, ChoyxonaPost, ChoyxonaPostLike, ChoyxonaPostRepost
from api.community import _map_post

async def check_mapped_post():
    async with AsyncSessionLocal() as session:
        # Get joxajon
        result = await session.execute(select(Student).where(Student.username == 'joxajon'))
        user = result.scalar_one_or_none()
        if not user:
            print("User joxajon not found")
            return

        print(f"User: {user.full_name}, Premium: {user.is_premium}")

        # Get one of his posts
        # Need eager load likes/reposts for _map_post
        from sqlalchemy.orm import selectinload
        stmt = select(ChoyxonaPost).options(
            selectinload(ChoyxonaPost.likes),
            selectinload(ChoyxonaPost.reposts)
        ).where(ChoyxonaPost.student_id == user.id).limit(1)
        
        res = await session.execute(stmt)
        post = res.scalar_one_or_none()
        
        if not post:
            print("No posts found for joxajon")
            return
            
        mapped = _map_post(post, user, user.id)
        print(f"Mapped Post author_is_premium: {mapped.author_is_premium}")
        
if __name__ == "__main__":
    asyncio.run(check_mapped_post())

import asyncio
from datetime import datetime
from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import ChoyxonaPost, Student
from api.community import view_post
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async with AsyncSessionLocal() as db:
        # Choose a random post and student
        post = await db.scalar(select(ChoyxonaPost).limit(1))
        student = await db.scalar(select(Student).where(Student.id == 3)) # Sanjar
        
        print(f"Testing view on post {post.id} with user {student.id}")
        
        # Test 1: First view
        res1 = await view_post(post.id, student, db)
        print(f"View 1 Result: {res1}")
        
        # Test 2: Immediate second view (should just update viewed_at and return same count)
        res2 = await view_post(post.id, student, db)
        print(f"View 2 Result: {res2}")
        
if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())

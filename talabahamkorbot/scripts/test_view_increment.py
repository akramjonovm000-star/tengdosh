import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, Student, Staff, ChoyxonaPostView
from api.community import get_post_by_id

async def test_view_logic():
    print("🧪 Testing Choyxona Post View Logic...")
    
    async with AsyncSessionLocal() as db:
        # 1. Get a post and a student
        post_result = await db.execute(select(ChoyxonaPost).limit(1))
        post = post_result.scalar_one_or_none()
        
        student_result = await db.execute(select(Student).limit(1))
        student = student_result.scalar_one_or_none()
        
        if not post or not student:
            print("❌ Post or Student not found in DB. Please create them first.")
            return

        print(f"Post ID: {post.id}, Student ID: {student.id}")
        initial_views = post.views_count
        print(f"Initial Views: {initial_views}")

        # 2. Call get_post_by_id (which increments views)
        print("Calling get_post_by_id for the first time...")
        await get_post_by_id(post.id, db, student)
        
        # Refresh and check
        await db.refresh(post)
        print(f"Views after 1st call: {post.views_count}")
        
        if post.views_count == initial_views + 1:
            print("✅ View incremented successfully for unique user.")
        else:
            print("❌ View increment failed or was not unique.")

        # 3. Call again with same user
        print("Calling get_post_by_id for the second time (same user)...")
        await get_post_by_id(post.id, db, student)
        await db.refresh(post)
        print(f"Views after 2nd call: {post.views_count}")
        
        if post.views_count == initial_views + 1:
            print("✅ View did NOT increment for same user. Correct.")
        else:
            print("❌ View incremented for same user! Bug.")

        # 4. Check ChoyxonaPostView record
        v_result = await db.execute(
            select(ChoyxonaPostView).where(
                ChoyxonaPostView.post_id == post.id,
                ChoyxonaPostView.student_id == student.id
            )
        )
        view_rec = v_result.scalar_one_or_none()
        if view_rec:
            print("✅ View record found in database.")
        else:
            print("❌ View record NOT found in database.")

if __name__ == "__main__":
    asyncio.run(test_view_logic())

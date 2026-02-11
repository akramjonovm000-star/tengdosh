import asyncio
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select, text
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, Student, ChoyxonaPostView

async def test_view_logic_standalone():
    print("🧪 Testing Choyxona Post View Logic (Standalone)...")
    
    async with AsyncSessionLocal() as db:
        # 1. Get a post and a student
        post_result = await db.execute(select(ChoyxonaPost).limit(1))
        post = post_result.scalar_one_or_none()
        
        student_result = await db.execute(select(Student).limit(1))
        student = student_result.scalar_one_or_none()
        
        if not post or not student:
            print("❌ Post or Student not found in DB. Please create them first.")
            return

        post_id = post.id
        student_id = student.id
        print(f"Post ID: {post_id}, Student ID: {student_id}")
        
        # Reset views count for testing
        post.views_count = 0
        # Delete existing views for this user/post
        await db.execute(text(f"DELETE FROM choyxona_post_views WHERE post_id={post_id} AND student_id={student_id}"))
        await db.commit()
        await db.refresh(post)
        
        initial_views = post.views_count
        print(f"Initial Views: {initial_views}")

        # --- SIMULATE LOGIC FROM api/community.py ---
        async def simulate_view(p_id, s_id):
            async with AsyncSessionLocal() as db_inner:
                p_inner = await db_inner.get(ChoyxonaPost, p_id)
                # Check uniqueness
                v_query = select(ChoyxonaPostView.id).where(
                    ChoyxonaPostView.post_id == p_id,
                    ChoyxonaPostView.student_id == s_id
                )
                v_result = await db_inner.execute(v_query.limit(1))
                if not v_result.scalar_one_or_none():
                    print(f"Adding new view for user {s_id} on post {p_id}")
                    new_view = ChoyxonaPostView(post_id=p_id, student_id=s_id)
                    db_inner.add(new_view)
                    # Atomic increment simulation
                    p_inner.views_count = ChoyxonaPost.views_count + 1
                    await db_inner.commit()
                    return True
                else:
                    print(f"View already exists for user {s_id}")
                    return False

        # 2. First View
        print("Triggering first view...")
        await simulate_view(post_id, student_id)
        
        await db.refresh(post)
        print(f"Views after 1st call: {post.views_count}")
        
        # 3. Second View (Same User)
        print("Triggering second view (same user)...")
        await simulate_view(post_id, student_id)
        
        await db.refresh(post)
        print(f"Views after 2nd call: {post.views_count}")

        if post.views_count == 1:
            print("✅ SUCCESS: View count logic works as expected (Unique tracking).")
        else:
            print(f"❌ FAILURE: View count is {post.views_count}, expected 1.")

if __name__ == "__main__":
    asyncio.run(test_view_logic_standalone())

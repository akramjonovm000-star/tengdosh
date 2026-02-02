import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student
from api.community import get_comments
from api.schemas import CommentResponseSchema

async def test_get_comments():
    async with AsyncSessionLocal() as session:
        # 1. Get a student to "act as"
        student = await session.get(Student, 730) # Rahimxonov
        if not student:
            print("Student 730 not found")
            return
            
        print(f"Testing get_comments for post 40 as student {student.id}")
        
        try:
            # Call the function directly
            comments = await get_comments(post_id=40, student=student, db=session)
            print(f"Successfully retrieved {len(comments)} comments")
            for c in comments:
                # Check if it serializes correctly
                # (Pydantic models will validate on init)
                print(f"Comment ID: {c.id}, Author: {c.author_name}")
        except Exception as e:
            import traceback
            print(f"Error in get_comments: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_comments())

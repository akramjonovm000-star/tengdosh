import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student, ChoyxonaPost, ChoyxonaComment

async def check_data():
    async with AsyncSessionLocal() as session:
        # Check Post 40 access info
        stmt = select(ChoyxonaPost).where(ChoyxonaPost.id == 40)
        post = await session.scalar(stmt)
        if post:
            print(f"Post 40 Context: Category={post.category_type}, Uni={post.target_university_id}, Fac={post.target_faculty_id}, Spec={post.target_specialty_name}")
        
        # Check student 730 info
        student = await session.get(Student, 730)
        if student:
             print(f"Student 730 Context: Uni={student.university_id}, Fac={student.faculty_id}, Spec={student.specialty_name}")

if __name__ == "__main__":
    asyncio.run(check_data())

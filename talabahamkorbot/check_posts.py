import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from database.db_connect import get_db
from database.models import ChoyxonaPost, Student
import asyncio

async def check_posts():
    print("Checking posts visibility...")
    async for db in get_db():
        # Get a test student
        student = await db.scalar(select(Student).limit(1))
        if not student:
            print("No students found!")
            return
            
        print(f"Test Student: {student.full_name} (ID: {student.id}, Uni: {student.university_id}, Fac: {student.faculty_id})")
        
        # Simulate 'university' category
        query = select(ChoyxonaPost).where(ChoyxonaPost.category_type == 'university')
        query = query.where(ChoyxonaPost.target_university_id == student.university_id)
        result = await db.execute(query)
        uni_posts = result.scalars().all()
        print(f"Visible 'university' posts: {len(uni_posts)}")
        
        # Simulate 'faculty' category
        query = select(ChoyxonaPost).where(ChoyxonaPost.category_type == 'faculty')
        query = query.where(ChoyxonaPost.target_university_id == student.university_id)
        if student.faculty_id:
            query = query.where(ChoyxonaPost.target_faculty_id == student.faculty_id)
        result = await db.execute(query)
        fac_posts = result.scalars().all()
        print(f"Visible 'faculty' posts: {len(fac_posts)}")
        
        break

if __name__ == "__main__":
    asyncio.run(check_posts())

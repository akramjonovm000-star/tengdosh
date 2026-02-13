import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from config import DATABASE_URL
from database.models import Staff, Student, StudentDocument
from api.management import get_mgmt_documents_archive

class MockStaff:
    def __init__(self, id, role, university_id=None):
        self.id = id
        self.role = role
        self.university_id = university_id

async def verify_stats():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Simulate Staff 27 (Developer)
        staff = MockStaff(id=27, role='developer')
        
        print(f"--- Hard Testing Archive API Logic ---")
        
        # We call the function logic (simplified since we don't want to mock Depends)
        # But we previously added logging to it, so running it here won't show logs in journal
        # Let's just run the actual function logic here
        from database.models import StaffRole
        from api.management import build_student_filter
        from sqlalchemy import and_, func, distinct
        
        category_filters = build_student_filter(staff)
        print(f"Filters: {category_filters}")
        
        # Main Query matching what we fixed
        stmt = select(StudentDocument).join(Student).where(and_(*category_filters))
        total_count = await session.scalar(select(func.count()).select_from(stmt.subquery()))
        print(f"Total Documents in Overall Scope: {total_count}")
        
        # Stats matching what we fixed
        student_count_stmt = select(func.count(distinct(Student.id))).where(and_(*category_filters))
        total_students_in_scope = await session.scalar(student_count_stmt)
        print(f"Students in Scope: {total_students_in_scope}")

        uploaded_students_stmt = select(func.count(distinct(StudentDocument.student_id))).join(Student).where(and_(*category_filters))
        students_with_uploads = await session.scalar(uploaded_students_stmt)
        print(f"Students with Uploads: {students_with_uploads}")

        total_docs_stmt = select(func.count(StudentDocument.id)).join(Student).where(and_(*category_filters, StudentDocument.file_type == "document"))
        total_docs = await session.scalar(total_docs_stmt)
        print(f"Total Documents (type=document): {total_docs}")

        # Check for Obyektivka specifically
        oby_stmt = stmt.where(StudentDocument.file_name.ilike("%Obyektivka%"))
        oby_count = await session.scalar(select(func.count()).select_from(oby_stmt.subquery()))
        print(f"Total Obyektivka files: {oby_count}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_stats())

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select, and_, func, distinct
from config import DATABASE_URL
from database.models import Staff, Student, StudentDocument
from api.management import build_student_filter

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
        
        print(f"--- Detailed Document Check ---")
        category_filters = build_student_filter(staff)
        
        # Check Total Documents JOINED with Student
        stmt = (
            select(StudentDocument)
            .join(Student)
            .where(and_(*category_filters))
            .options(selectinload(StudentDocument.student))
        )
        
        res = await session.execute(stmt)
        all_docs = res.scalars().all()
        
        print(f"Total Documents Found: {len(all_docs)}")
        
        print("\n--- Document Details (First 20) ---")
        for i, doc in enumerate(all_docs[:20]):
            print(f"{i+1}. ID: {doc.id} | Title: '{doc.file_name}' | Type: '{doc.file_type}' | UploadedBy: '{doc.uploaded_by}' | Student: {doc.student.full_name} ({doc.student_id})")
            
        print("\n--- 'Obyektivka' Specific Check ---")
        oby_docs = [d for d in all_docs if 'obyektivka' in d.file_name.lower()]
        print(f"Found {len(oby_docs)} Obyektivka documents:")
        for doc in oby_docs:
             print(f"- ID: {doc.id} | Title: '{doc.file_name}' | FileID: {doc.telegram_file_id[:10]}... | Student: {doc.student.full_name}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_stats())

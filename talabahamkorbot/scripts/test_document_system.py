import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentDocument, ActivityLog, ActivityType, Faculty

async def test_document_system():
    async with AsyncSessionLocal() as db:
        print("--- Testing Student Document System ---")
        
        # 1. Setup Test Student
        print("1. Setting up test student...")
        test_hemis_id = "TEST_DOC_SYSTEM_001"
        student = await db.scalar(select(Student).where(Student.hemis_id == test_hemis_id))
        
        if not student:
            student = Student(
                hemis_id=test_hemis_id,
                full_name="Test Student For Docs",
                hemis_login="test_docs_login",
                faculty_name="Test Faculty",
                group_number="TEST-001"
            )
            db.add(student)
            await db.commit()
            await db.refresh(student)
            print(f"Created test student: {student.id}")
        else:
            print(f"Using existing test student: {student.id}")

        # 2. Simulate Upload (Direct DB Insert as API does)
        print("2. Simulating Document Upload...")
        doc = StudentDocument(
            student_id=student.id,
            file_name="test_reference.pdf",
            description="Ma'lumotnoma",
            file_id="TEST_FILE_ID_12345",
            file_type="document",
            status="active"
        )
        db.add(doc)
        
        # Create Activity Log
        log = ActivityLog(
            student_id=student.id,
            faculty_id=student.faculty_id,
            activity_type=ActivityType.DOCUMENT,
            meta_data={"file_name": doc.file_name}
        )
        db.add(log)
        await db.commit()
        await db.refresh(doc)
        print(f"Created document: {doc.id}")

        # 3. Verify Student View (Mocking get_my_documents query)
        print("3. Verifying Student View...")
        stmt = select(StudentDocument).where(StudentDocument.student_id == student.id)
        my_docs = (await db.execute(stmt)).scalars().all()
        
        found = False
        for d in my_docs:
            if d.id == doc.id:
                found = True
                print(f"SUCCESS: Found document in 'My Documents' - ID: {d.id}, Name: {d.file_name}")
                break
        
        if not found:
            print("FAILURE: Document not found in Student View")

        # 4. Verify Management Archive View (Mocking get_mgmt_documents_archive query)
        print("4. Verifying Management Archive...")
        stmt_mgmt = select(StudentDocument).where(StudentDocument.id == doc.id)
        mgmt_doc = (await db.execute(stmt_mgmt)).scalar()
        
        if mgmt_doc:
            print(f"SUCCESS: Found document in Management Archive - ID: {mgmt_doc.id}, Name: {mgmt_doc.file_name}")
        else:
            print("FAILURE: Document not found in Management Archive")

        # 5. Cleanup
        print("5. Cleaning up...")
        await db.delete(doc)
        await db.delete(log)
        # Optional: delete student if created, but keeping for now or delete
        await db.delete(student)
        await db.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(test_document_system())

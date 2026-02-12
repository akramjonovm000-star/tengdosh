import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, or_
from database.db_connect import AsyncSessionLocal
from database.models import Student, ActivityLog, ActivityType, Faculty

async def check_docs():
    async with AsyncSessionLocal() as db:
        print("Checking for Jurnalistika Documents...")
        
        # 1. Find Jurnalistika Faculty
        stmt = select(Faculty).where(or_(Faculty.name.ilike("%Jurnalistika%"), Faculty.id == 36))
        faculty = (await db.execute(stmt)).scalar()
        
        if not faculty:
            print("ERROR: Jurnalistika faculty not found!")
            return

        print(f"Target Faculty: {faculty.name} (ID: {faculty.id})")
        
        # 2. Get Students
        stmt = select(Student.id).where(or_(Student.faculty_id == faculty.id, Student.faculty_name.ilike("%Jurnalistika%")))
        student_ids = (await db.execute(stmt)).scalars().all()
        
        print(f"Found {len(student_ids)} students in Jurnalistika.")
        
        if not student_ids:
            return

        # 3. Check Activity Logs (Certificates/Documents)
        stmt = select(ActivityLog.activity_type, func.count(ActivityLog.id))\
            .where(ActivityLog.student_id.in_(student_ids))\
            .where(ActivityLog.activity_type.in_([ActivityType.CERTIFICATE, ActivityType.DOCUMENT]))\
            .group_by(ActivityLog.activity_type)
            
        logs = (await db.execute(stmt)).all()
        
        print("\n--- Activity Log Check ---")
        if logs:
            for type_, count in logs:
                print(f"- {type_}: {count} uploaded")
        else:
            print("No 'certificate' or 'document' activities found.")
            
        # 4. Check Student Profile Images (Optional check)
        stmt = select(func.count(Student.id)).where(Student.id.in_(student_ids)).where(Student.image_url != None)
        has_image = (await db.execute(stmt)).scalar()
        print(f"\n--- Profile Check ---")
        print(f"Students with image_url: {has_image}")

if __name__ == "__main__":
    asyncio.run(check_docs())

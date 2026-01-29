import asyncio
import json
from services.hemis_service import HemisService
from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student

async def probe():
    async with AsyncSessionLocal() as session:
        student = await session.scalar(select(Student).where(Student.hemis_token != None).limit(1))
        if not student: return print("No student")
        
        token = student.hemis_token
        print(f"Student: {student.full_name}")
        
        # Get Subjects
        subjects = await HemisService.get_student_subject_list(token)
        if subjects:
            print(f"Found {len(subjects)} subjects")
            # Dump first subject
            print("--- Subject Sample ---")
            print(json.dumps(subjects[0], indent=2))
        else:
            print("No subjects")

        # Get Absence
        absence = await HemisService.get_student_absence(token)
        # absence returns (total, exc, unexc, items)
        if absence and len(absence) > 3:
             items = absence[3]
             if items:
                 print("--- Absence Sample ---")
                 print(json.dumps(items[0], indent=2))

if __name__ == "__main__":
    asyncio.run(probe())

import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from services.hemis_service import HemisService
from services.gpa_calculator import GPACalculator

# Setup Logging
logging.basicConfig(level=logging.INFO)

SEMESTER_CODE = "11"

async def debug_shahribonu():
    async with AsyncSessionLocal() as session:
        # Find Shahribonu
        stmt = select(Student).where(Student.full_name.like("%Shahribonu%"))
        result = await session.execute(stmt)
        student = result.scalars().first()
        
        if not student:
            print("Shahribonu not found in DB")
            return
            
        print(f"Checking Student: {student.full_name} (ID: {student.id})")
        print(f"Stored GPA: {student.gpa}")
        
        token = student.hemis_token
        if not token:
            print("No token found")
            return
            
        print("Fetching subjects...")
        subjects = await HemisService.get_student_subject_list(token, semester_code=SEMESTER_CODE)
        
        if not subjects:
            print("No subjects returned from HEMIS")
            return
            
        print(f"Found {len(subjects)} subjects:")
        for s in subjects:
            name = s.get("subject", {}).get("name") or s.get("curriculumSubject", {}).get("subject", {}).get("name")
            credit = s.get("credit") or s.get("curriculumSubject", {}).get("credit")
            
            # Grade details
            overall = s.get("overallScore")
            grade = 0
            if isinstance(overall, dict):
                grade = overall.get("grade")
            elif overall:
                grade = overall
                
            print(f" - {name} | Credit: {credit} | Grade: {grade} (Raw Overall: {overall})")
            
        print("\n--- Running Calculator ---")
        gpa_res = GPACalculator.calculate_gpa(subjects, exclude_in_progress=False)
        print(f"Calculated GPA: {gpa_res.gpa}")
        print(f"Details: Total Credit: {gpa_res.total_credits}, Total Points: {gpa_res.total_points}")

if __name__ == "__main__":
    asyncio.run(debug_shahribonu())

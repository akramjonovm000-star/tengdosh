
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student
from services.hemis_service import HemisService
from services.gpa_calculator import GPACalculator

async def main():
    async with AsyncSessionLocal() as session:
        s = await session.scalar(select(Student).where(Student.hemis_login == '395251101411'))
        if not s:
            print("User not found")
            return

        print(f"Checking GPA for Semester 11 (Previous)...")
        subjects = await HemisService.get_student_subject_list(s.hemis_token, semester_code="11")
        print(f"Subjects Breakdown:")
        for sub in subjects:
             name = sub.get("subject", {}).get("name")
             score = sub.get("overallScore")
             print(f" - {name}: {score}")

        result = GPACalculator.calculate_gpa(subjects)
        print(f"Calculated GPA: {result.gpa}")
        print(f"Total Credits: {result.total_credits}")

if __name__ == "__main__":
    asyncio.run(main())

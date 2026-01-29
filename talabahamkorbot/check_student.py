import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_student():
    async with AsyncSessionLocal() as db:
        print("Checking Student 730...")
        result = await db.execute(select(Student).where(Student.id == 730))
        student = result.scalar_one_or_none()
        
        if student:
            print(f"Student: {student.full_name}")
            print(f"University ID: {student.university_id}")
            print(f"Faculty ID: {student.faculty_id}")
            print(f"Specialty: {student.specialty_name}")
        else:
            print("Student not found.")

if __name__ == "__main__":
    asyncio.run(check_student())

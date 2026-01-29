import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_db():
    async with AsyncSessionLocal() as session:
        # Get the specific student from screenshot
        result = await session.execute(select(Student).where(Student.hemis_login == '395251101411'))
        student = result.scalar_one_or_none()
        
        if student:
            print(f"ID: {student.id}")
            print(f"Full Name: {student.full_name}")
            print(f"Short Name: {student.short_name}")
            print(f"University: {student.university_name}")
            print(f"Faculty: {student.faculty_name}")
            print(f"Specialty: {student.specialty_name}")
            print(f"Semester: {student.semester_name}")
            print(f"Group: {student.group_number}")
            print(f"Image: {student.image_url}")
            print(f"HEMIS Login: {student.hemis_login}")
        else:
            print("No students found.")

if __name__ == "__main__":
    asyncio.run(check_db())

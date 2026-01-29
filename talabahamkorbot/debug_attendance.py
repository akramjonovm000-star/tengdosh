import asyncio
from services.hemis_service import HemisService
from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student, TgAccount

async def debug_attendance():
    # Hardcode a student ID or find one active
    async with AsyncSessionLocal() as session:
        # Find a student with token
        stmt = select(Student).where(Student.hemis_token != None).limit(1)
        student = await session.scalar(stmt)
        
        if not student:
            print("No student found")
            return

        print(f"Testing Student: {student.full_name} ({student.id})")
        token = student.hemis_token
        
        # Test Default
        print("--- Default (Current) ---")
        _, _, _, data = await HemisService.get_student_absence(token)
        print(f"Items: {len(data)}")
        if data: print(data[0])
        else: print("Valid Empty Response")
        
        # Test Semester 11
        print("--- Semester 11 ---")
        _, _, _, data_11 = await HemisService.get_student_absence(token, semester_code="11")
        print(f"Items: {len(data_11)}")

        # Test Semester 12
        print("--- Semester 12 ---")
        _, _, _, data_12 = await HemisService.get_student_absence(token, semester_code="12")
        print(f"Items: {len(data_12)}")
        
        # Test Semester 13
        print("--- Semester 13 ---")
        _, _, _, data_13 = await HemisService.get_student_absence(token, semester_code="13")
        print(f"Items: {len(data_13)}")

if __name__ == "__main__":
    asyncio.run(debug_attendance())

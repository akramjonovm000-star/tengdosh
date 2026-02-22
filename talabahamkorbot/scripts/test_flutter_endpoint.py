import asyncio
import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import AsyncSessionLocal
from database.models import Student
from services.hemis_service import HemisService
from services.university_service import UniversityService

async def main():
    login = "395251101417"
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        student = await session.scalar(select(Student).where(Student.hemis_login == login))
        
        if not student:
            print("Student not found in DB.")
            return

        base_url = UniversityService.get_api_url(login)
        print(f"Token: {student.hemis_token[:20]}...")
        
        data = await HemisService.get_student_contract(student.hemis_token, student_id=student.id, force_refresh=True, base_url=base_url)
        print(f"Direct Service call returns type: {type(data)}")
        
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())

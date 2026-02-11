import asyncio
import sys
import os
from sqlalchemy import select

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import get_session_factory
from database.models import Student

TARGET_NAME = "OMONOVA AZIZA ULUG‘BEK QIZI"

async def get_token():
    AsyncSessionLocal = get_session_factory()
    async with AsyncSessionLocal() as session:
        stmt = select(Student).where(Student.full_name == TARGET_NAME)
        result = await session.execute(stmt)
        student = result.scalars().first()
        
        if student:
            print(f"FOUND: {student.full_name}")
            print(f"TOKEN: {student.hemis_token}")
        else:
            print("Student not found.")

if __name__ == "__main__":
    asyncio.run(get_token())

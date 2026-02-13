
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as session:
        login = "395251101412"
        stmt = select(Student).where(Student.hemis_login == login)
        student = (await session.execute(stmt)).scalar_one_or_none()
        
        if student:
            print(f"ID: {student.id}, Name: {student.full_name}, Login: {student.hemis_login}, Role: {getattr(student, 'role', 'N/A')}")
        else:
            print(f"Student with login {login} not found!")

if __name__ == "__main__":
    asyncio.run(run())

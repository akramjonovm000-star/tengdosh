import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student

async def find_ids():
    async with AsyncSessionLocal() as session:
        ids = ["395251101411", "395251101397", "395251101417"]
        for hid in ids:
            stmt = select(Student).where(Student.hemis_login == hid)
            student = await session.scalar(stmt)
            if student:
                print(f"Found Student with HEMIS {hid}: ID {student.id}, Name {student.full_name}")
            else:
                print(f"Student with HEMIS {hid} NOT FOUND")

if __name__ == "__main__":
    asyncio.run(find_ids())

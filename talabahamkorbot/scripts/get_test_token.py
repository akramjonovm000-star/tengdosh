import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'talabahamkorbot'))

from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Student, User
from talabahamkorbot.api.auth import create_access_token

async def get_test_token():
    async with AsyncSessionLocal() as session:
        # Get student 730
        student = await session.get(Student, 730)
        # Auth token usually requires hemis_login or student_id match
        token = create_access_token(data={"sub": str(student.hemis_login), "role": "student"})
        print(f"Token for {student.full_name}:")
        print(token)

if __name__ == "__main__":
    asyncio.run(get_test_token())

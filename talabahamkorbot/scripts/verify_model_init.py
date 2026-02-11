import asyncio
import sys
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def verify():
    print('--- Testing Student Model Init ---')
    try:
        dummy = Student(
            hemis_id="TEST_ID",
            hemis_login="TEST_LOGIN_UNIQUE",
            full_name="TEST STUDENT",
            university_id=1,
            faculty_id=1,
            # No other fields
        )
        print("Student object created successfully in memory.")
    except Exception as e:
        print(f"ERROR creating Student object: {e}")

asyncio.run(verify())

import asyncio
import os
import sys
import json

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'talabahamkorbot'))

from sqlalchemy import select
from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Student, User
from talabahamkorbot.api.dashboard import get_dashboard_stats
from talabahamkorbot.api.schemas import StudentDashboardSchema

async def test_api_response():
    async with AsyncSessionLocal() as session:
        # Get student ID 730 (who has active election in my debug script)
        student = await session.get(Student, 730)
        if not student:
            print("Student 730 not found")
            return

        print(f"Testing Dashboard API for: {student.full_name} (ID: {student.id})")
        
        # Simulate calling the endpoint function directly
        # We need to mock 'db' and 'student' depends
        response = await get_dashboard_stats(refresh=False, student=student, db=session)
        
        # response is a StudentDashboardSchema object
        print("API Response Body:")
        print(json.dumps(response.model_dump(), indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_api_response())

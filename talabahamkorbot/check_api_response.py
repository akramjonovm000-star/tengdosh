
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student
from api.dashboard import get_dashboard_stats
# We need to mock dependencies
from unittest.mock import AsyncMock

async def main():
    async with AsyncSessionLocal() as session:
        s = await session.scalar(select(Student).where(Student.hemis_login == '395251101411'))
        if not s:
            print("User not found")
            return

        print(f"Testing Dashboard API for {s.full_name}")
        try:
            # Direct call to the function logic? 
            # Ideally we run the function but we need valid DB session dependency
            result = await get_dashboard_stats(refresh=False, student=s, db=session)
            print(f"API Returned GPA: {result.gpa}")
        except Exception as e:
            print(f"Error calling API func: {e}")

if __name__ == "__main__":
    asyncio.run(main())

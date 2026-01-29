
import asyncio
import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student
from api.dashboard import get_dashboard_stats

async def main():
    async with AsyncSessionLocal() as session:
        s = await session.scalar(select(Student).where(Student.hemis_login == '395251101411'))
        if not s:
            print("User not found")
            return

        print(f"Current DB GPA: {s.gpa}")
        
        print("Calling get_dashboard_stats(refresh=True)...")
        try:
            # We assume get_dashboard_stats handles the logic internally
            result = await get_dashboard_stats(refresh=True, student=s, db=session)
            print(f"Result GPA: {result.gpa}")
            
            # Check DB again
            await session.refresh(s)
            print(f"Post-Refresh DB GPA: {s.gpa}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

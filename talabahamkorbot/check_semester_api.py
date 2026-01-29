
import asyncio
import sys
import os

# Add path to find modules
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from sqlalchemy import select
from database.models import Student
from services.hemis_service import HemisService

async def main():
    async with AsyncSessionLocal() as session:
        # Get user
        s = await session.scalar(select(Student).where(Student.hemis_login == '395251101411'))
        if not s:
            print("User not found")
            return

        print(f"DB Semester: {s.semester_name}")
        print(f"Token: {s.hemis_token[:10]}...")

        # Get Me
        me = await HemisService.get_me(s.hemis_token)
        if me:
            print(f"HEMIS Me Semester: {me.get('semester')}")
        else:
            print("Failed to get ME")

        # Get Semesters
        sems = await HemisService.get_semester_list(s.hemis_token)
        print(f"Semesters Limit 5: {sems[:5]}")
        
        # Check if any semester is "current"
        for sem in sems:
            if sem.get('current') is True:
                print(f"CURRENT SEMESTER FLAG FOUND: {sem}")

if __name__ == "__main__":
    asyncio.run(main())

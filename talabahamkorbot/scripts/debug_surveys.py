import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select
from services.hemis_service import HemisService

async def main():
    async with AsyncSessionLocal() as session:
        # Get a student with a token (preferably one who should have surveys)
        result = await session.execute(select(Student).where(Student.hemis_token.isnot(None)).limit(1))
        student = result.scalar_one_or_none()
        
        if not student:
            print("No student with token found.")
            return

        print(f"Testing for student: {student.full_name} ({student.id})")
        
        # Test 1: Check Auth Status
        status = await HemisService.check_auth_status(student.hemis_token)
        print(f"Auth Status: {status}")
        
        if status != "OK":
            print("Token expired or invalid. Cannot test surveys.")
            # Try to re-login if we had credentials (we don't store password plain, so skipping)
            return

        # Test 2: Fetch Surveys
        print("\nFetching Surveys...")
        try:
            surveys = await HemisService.get_student_surveys(student.hemis_token)
            import json
            print(json.dumps(surveys, indent=2, ensure_ascii=False))
            
            if surveys is None:
                print("Result: None (Error occurred)")
            elif isinstance(surveys, dict) and 'data' in surveys:
                data = surveys['data']
                print(f"\nStats: {data.get('stats')}")
                print(f"Not Started: {len(data.get('not_started', []) or [])}")
                print(f"In Progress: {len(data.get('in_progress', []) or [])}")
                print(f"Finished: {len(data.get('finished', []) or [])}")
            else:
                print("Unexpected response structure.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

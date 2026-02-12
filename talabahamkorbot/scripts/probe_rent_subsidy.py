import asyncio
import sys
import os
import httpx
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import get_session
from database.models import Student
from sqlalchemy import select
from services.hemis_service import HemisService
from services.university_service import UniversityService

async def probe_rent_subsidy():
    async for db in get_session():
        # Get a student with a token
        # Try to find a student who might actually HAVE subsidy data if possible, 
        # but for now just any valid student.
        target_id = "395251101397"
        stmt = select(Student).where(Student.hemis_id == target_id)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()
        
        if not student:
            print(f"No student found with ID {target_id}. Trying hemis_login...")
            stmt = select(Student).where(Student.hemis_login == target_id)
            result = await db.execute(stmt)
            student = result.scalar_one_or_none()

        if not student:
             print(f"Still no student found for {target_id}")
             return

        students = [student]


        print(f"Found {len(students)} students to test.")

        for student in students:
            print(f"\n--- Testing with student: {student.full_name} ({student.hemis_id}) ---")
            
            base_url = UniversityService.get_api_url(student.hemis_login) or HemisService.BASE_URL
            client = await HemisService.get_client()
            headers = HemisService.get_headers(student.hemis_token)
            
            url = f"{base_url}/billing/subsidy-rent-report"
            
            # Try current year and next year
            # Semester is 2025-2026 implies eduYear might be 2025? 
            # Current date is Feb 2026.
            # Academic year for Feb 2026 is likely 2025 (starts Sep 2025).
            
            years = [2024, 2025, 2026]
            
            for year in years:
                payload = {"eduYear": year}
                print(f"POST {url} with {payload}...")
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    print(f"Status: {resp.status_code}")
                    if resp.status_code == 200:
                        print(f"Body: {resp.text}")
                    else:
                        print(f"Error Body: {resp.text}")
                except Exception as e:
                    print(f"Request Error: {e}")
            
            # Stop after first successful 200 OK that has data (if any)
            # For now just stop after first student to avoid spamming if it works.
            break

if __name__ == "__main__":
    asyncio.run(probe_rent_subsidy())

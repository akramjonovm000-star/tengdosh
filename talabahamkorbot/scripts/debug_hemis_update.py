import asyncio
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import get_session
from database.models import Student
from sqlalchemy import select
from services.hemis_service import HemisService
from services.university_service import UniversityService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def probe():
    async for db in get_session():
        # Get a student with a token
        result = await db.execute(select(Student).where(Student.hemis_token != None).limit(1))
        student = result.scalar_one_or_none()
        
        if not student:
            print("No student found with token")
            return

        print(f"Testing with student: {student.full_name} ({student.hemis_id})")
        base_url = UniversityService.get_api_url(student.hemis_login) or HemisService.BASE_URL
        print(f"Base URL: {base_url}")
        
        headers = HemisService.get_headers(student.hemis_token)
        client = await HemisService.get_client()

        # Test Data (using existing data to avoid messing up too much, or minor change)
        # We'll just try to "update" the phone to the SAME value or append a dot if possible (but validation might fail).
        # Better just send necessary fields.
        
        phone = student.phone or "998901234567"
        email = student.email or "test@example.com"
        
        payload = {
            "phone": phone,
            "email": email
        }
        
        print(f"\n--- Probing POST /account/update ---")
        url_update = f"{base_url}/account/update"
        try:
            resp = await client.post(url_update, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        print(f"\n--- Probing POST /account/me (with phone/email) ---")
        url_me = f"{base_url}/account/me"
        try:
            resp = await client.post(url_me, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Check if PUT works
        print(f"\n--- Probing PUT /account/me (with phone/email) ---")
        try:
            resp = await client.put(url_me, json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(probe())

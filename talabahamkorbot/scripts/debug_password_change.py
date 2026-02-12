import asyncio
import sys
import os
import httpx

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import get_session
from database.models import Student
from sqlalchemy import select
from services.hemis_service import HemisService
from services.university_service import UniversityService

async def probe_password_endpoints():
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
        
        # Candidate Endpoints to Text
        candidates = [
            "/account/password",
            "/account/change-password",
            "/account/reset-password",
            "/user/password",
            "/user/change-password",
            "/student/password",
            "/student/change-password",
            "/profile/password",
            "/profile/change-password"
        ]
        
        payloads = [
            {"password": "WrongPassword123", "password_confirm": "WrongPassword123"},
            {"old_password": "RealOldPassword", "password": "WrongPassword123", "password_confirm": "WrongPassword123"},
            {"current_password": "RealOldPassword", "new_password": "WrongPassword123", "new_password_confirm": "WrongPassword123"},
             {"password": "WrongPassword123", "confirmation": "WrongPassword123"},
        ]
        
        # 1. Probe Candidates
        print("\n--- Probing Candidate Endpoints ---")
        for endpoint in candidates:
            url = f"{base_url}{endpoint}"
            print(f"Testing POST {url}...")
            try:
                for p in payloads:
                    resp = await client.post(url, json=p, headers=headers)
                    if resp.status_code != 404:
                         print(f"[FOUND?] {url} returned {resp.status_code}")
                         print(f"Body: {resp.text}")
                         break # Stop payloads if endpoint exists
            except Exception as e:
                print(f"Error: {e}")

        # 2. Retry /account/update with specific password payloads (maybe we missed a key?)
        print("\n--- Retrying POST /account/update with Validations ---")
        url_update = f"{base_url}/account/update"
        
        # Test 1: Standard Password Change (New + Confirm + Old)
        p1 = {
             "password": "NewPassword123",
             "password_confirm": "NewPassword123",
             "current_password": "OldPassword123"
        }
        # Test 2: Variation key names
        p2 = {
             "password": "NewPassword123",
             "confirmation": "NewPassword123",
             "old_password": "OldPassword123" 
        }
        # Test 3: Maybe inside 'Student' wrapper?
        p3 = {
            "Student": {
                 "password": "NewPassword123",
                 "password_confirm": "NewPassword123",
                 "current_password": "OldPassword123"
            }
        }
        
        for i, p in enumerate([p1, p2, p3]):
            print(f"Testing Payload {i+1}...")
            try:
                 resp = await client.post(url_update, json=p, headers=headers)
                 print(f"Status: {resp.status_code}")
                 print(f"Body: {resp.text}")
            except: pass

        # 3. Test Form Data with _method override (PHP/Laravel style)
        print("\n--- Retrying POST /account/update with Form Data & _method ---")
        
        # Test 4: Form Data with _method=PUT
        p4 = {
             "_method": "PUT",
             "password": "NewPassword123",
             "password_confirm": "NewPassword123"
        }
        
        # Test 5: Form Data with _method=PATCH
        p5 = {
             "_method": "PATCH",
             "password": "NewPassword123",
             "password_confirm": "NewPassword123"
        }

        # Test 6: Pure Form Data (no json)
        p6 = {
             "password": "NewPassword123",
             "password_confirm": "NewPassword123"
        }

        for i, p in enumerate([p4, p5, p6]):
             print(f"Testing Form Payload {i+4}...")
             try:
                 # Remove Content-Type to let httpx set it for form data
                 h = headers.copy()
                 if "Content-Type" in h: del h["Content-Type"]
                 
                 resp = await client.post(url_update, data=p, headers=h)
                 print(f"Status: {resp.status_code}")
                 print(f"Body: {resp.text}")
             except Exception as e:
                 print(f"Error: {e}")

        # 4. Probing OAuth/API Endpoints
        print("\n--- Probing OAuth/API Endpoints ---")
        oauth_candidates = [
            "/oauth/api/user/password",
            "/oauth/api/user/change-password",
            "/oauth/api/user/update-password",
            "/api/user/password",
            "/api/user/change-password",
            "/oauth/api/user/me/password" 
        ]
        
        # Base usually includes /rest/v1, we need to strip it to get root
        # e.g. https://student.jmcu.uz/rest/v1 -> https://student.jmcu.uz
        root_url = base_url.split("/rest/v1")[0]
        
        # 5. Probing /oauth/api/user for UPDATE (maybe it accepts POST?)
        print("\n--- Probing /oauth/api/user for UPDATE ---")
        url_user = f"{root_url}/oauth/api/user"
        try:
             # Try simple password payload
             resp = await client.post(url_user, json={"password": "NewPassword123"}, headers=headers)
             print(f"POST {url_user} Status: {resp.status_code}")
             print(f"Body: {resp.text}")
             
             # Try PUT
             resp = await client.put(url_user, json={"password": "NewPassword123"}, headers=headers)
             print(f"PUT {url_user} Status: {resp.status_code}")
             print(f"Body: {resp.text}")
        except Exception as e:
                print(f"Error probing {url_user}: {e}")

        # 6. Probing /oauth/api/user/update
        print("\n--- Probing /oauth/api/user/update ---")
        url_user_update = f"{root_url}/oauth/api/user/update"
        try:
             resp = await client.post(url_user_update, json={"password": "NewPassword123"}, headers=headers)
             print(f"POST {url_user_update} Status: {resp.status_code}")
             print(f"Body: {resp.text}")
        except Exception as e:
                print(f"Error probing {url_user_update}: {e}")

if __name__ == "__main__":
    asyncio.run(probe_password_endpoints())

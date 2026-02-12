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
        
        url_me = f"{base_url}/account/me"
        url_update = f"{base_url}/account/update"

        current_phone = student.phone or "998901234567"
        if len(current_phone) > 5:
            new_phone = current_phone[:-1] + ("1" if current_phone[-1] != "1" else "2")
        else:
            new_phone = "998901234567"

        # 1. Test PUT /account/me (JSON)
        print(f"\n--- 1. Probing PUT /account/me (JSON) ---")
        payload_me = {"phone": new_phone, "email": student.email or ""}
        try:
            resp = await client.put(url_me, json=payload_me, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                 data = resp.json().get("data", {})
                 print(f"Server Phone: {data.get('phone')} (Sent: {new_phone})")
                 if data.get("phone") == new_phone: print("SUCCESS: PUT /account/me Updated!")
            else:
                 print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # 2. Test POST /account/update (Form Data)
        print(f"\n--- 2. Probing POST /account/update (Form Data) ---")
        payload_update = {"phone": current_phone, "email": student.email or ""}
        try:
            # removing Content-Type header to let httpx set it for data=
            h = headers.copy()
            if "Content-Type" in h: del h["Content-Type"]
            
            resp = await client.post(url_update, data=payload_update, headers=h)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # 3. Test POST /account/me (Form Data)
        print(f"\n--- 3. Probing POST /account/me (Form Data) ---")
        try:
            h = headers.copy()
            if "Content-Type" in h: del h["Content-Type"]
            
            resp = await client.post(url_me, data=payload_me, headers=h)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                 data = resp.json().get("data", {})
                 print(f"Server Phone: {data.get('phone')} (Sent: {new_phone})")
                 if data.get("phone") == new_phone: print("SUCCESS: POST /account/me (Form) Updated!")
            else:
                 print(f"Body: {resp.text}")
        except Exception as e:
             print(f"Error: {e}")
             
        # 4. Test POST /account/update (Form Data + Password)
        print(f"\n--- 4. Probing POST /account/update (Form Data + Password) ---")
        payload_update_pass = {"phone": current_phone, "password": "WrongPassword123"}
        try:
            h = headers.copy()
            if "Content-Type" in h: del h["Content-Type"]
            resp = await client.post(url_update, data=payload_update_pass, headers=h)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # 5. Test POST /account/update with Wrapped Payloads (JSON)
        print(f"\n--- 5. Probing POST /account/update (Wrapped JSON) ---")
        wrappers = ["Student", "Account", "User", "data", "model"]
        for w in wrappers:
            print(f"Testing wrapper: {w}")
            payload_wrapped = {w: {"phone": current_phone, "email": student.email}}
            try:
                resp = await client.post(url_update, json=payload_wrapped, headers=headers)
                print(f"Status: {resp.status_code}, Body: {resp.text}")
            except: pass

        # 7. Test POST /account/me with Confirmation (Suspect this causes 400)
        print(f"\n--- 7. Probing POST /account/me (Phone + Password + Confirmation) ---")
        payload_me_confirm = {
            "phone": current_phone,
            "email": student.email or "",
            "password": "WrongPassword123",
            "confirmation": "WrongPassword123" 
        }
        try:
             resp = await client.post(url_me, json=payload_me_confirm, headers=headers)
             print(f"Status: {resp.status_code}, Body: {resp.text}")
        except: pass
        
        print(f"\n--- 8. Probing POST /account/me (Phone + Password + password_confirm) ---")
        payload_me_pc = {
            "phone": current_phone,
            "email": student.email or "",
            "password": "WrongPassword123",
            "password_confirm": "WrongPassword123" 
        }
        try:
             resp = await client.post(url_me, json=payload_me_pc, headers=headers)
             print(f"Status: {resp.status_code}, Body: {resp.text}")
        except: pass
        
        # 10. Probing POST /account/me (PASSWORD ONLY) - This is what current code does
        print(f"\n--- 10. Probing POST /account/me (Password ONLY) ---")
        try:
             resp = await client.post(url_me, json={"password": "WrongPassword123"}, headers=headers)
             print(f"Status: {resp.status_code}")
             if resp.status_code != 200:
                 print(f"Body: {resp.text}")
        except: pass

        # 11. Probing POST /account/me (Password + Confirm ONLY)
        print(f"\n--- 11. Probing POST /account/me (Password + Confirm ONLY) ---")
        try:
             resp = await client.post(url_me, json={"password": "WrongPassword123", "password_confirm": "WrongPassword123"}, headers=headers)
             print(f"Status: {resp.status_code}")
             if resp.status_code != 200:
                 print(f"Body: {resp.text}")
        except: pass

        # 12. Probing POST /account/me (Password + Current Phone/Email)
        print(f"\n--- 12. Probing POST /account/me (Password + Phone + Email) ---")
        try:
             payload_full = {
                 "password": "WrongPassword123",
                 "phone": current_phone,
                 "email": student.email or ""
             }
             resp = await client.post(url_me, json=payload_full, headers=headers)
             print(f"Status: {resp.status_code}")
             if resp.status_code != 200:
                 print(f"Body: {resp.text}")
        except: pass

        # 13. Call HemisService.change_password directly
        print(f"\n--- 13. Calling HemisService.change_password directly ---")
        try:
             # We need to mock the client or just call it if it uses the singleton
             # The method gets its own client.
             # We need to inspect the response inside api, but here we can only see result.
             # So we will modify the Service or rely on the script to mimic it exactly.
             
             # Let's mimic what HemisService.change_password does but PRINT the body
             print("Mimicking HemisService.change_password logic to see BODY:")
             url_me = f"{base_url}/account/me"
             payload_pass = {"password": "WrongPassword123"}
             resp = await client.post(url_me, json=payload_pass, headers=headers)
             print(f"Status: {resp.status_code}")
             print(f"Body: {resp.text}")
             
        except Exception as e:
             print(f"Service Call Error: {e}")

if __name__ == "__main__":
    asyncio.run(probe())

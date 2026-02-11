import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TgAccount

async def check_me_response():
    async with AsyncSessionLocal() as db:
        print("Fetching Staff ID 40...")
        staff = await db.get(Staff, 40)
        
        if not staff:
            print("Staff 40 not found!")
            return

        print(f"Staff Object: {staff}")
        print(f"Image URL in DB: {staff.image_url}")
        
        # Simulate /me logic
        h_login = getattr(staff, 'hemis_login', '')
        staff_id = getattr(staff, 'employee_id_number', None) or str(staff.hemis_id) if staff.hemis_id else h_login
        
        response = {
             "id": staff.id,
             "full_name": staff.full_name,
             "image": getattr(staff, 'image_url', None),
             "image_url": getattr(staff, 'image_url', None),
             "hemis_id": staff_id,
        }
        
        print("-" * 20)
        print(f"Simulated /me Response: {response}")
        print("-" * 20)
        
        # Validating what the frontend likely sees
        if response['image_url']:
             print("SUCCESS: Image URL is present.")
        else:
             print("FAILURE: Image URL is missing or None.")

if __name__ == "__main__":
    asyncio.run(check_me_response())

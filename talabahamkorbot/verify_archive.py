
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, Student

async def main():
    async with AsyncSessionLocal() as db:
        # We need a management staff for the Depends(get_current_student)
        # Let's find one or mock it
        staff = await db.get(Student, 1741) # Using a student as 'staff' depends mock
        if not staff:
            print("No test student found")
            return
            
        # Manually patching roles for test
        staff.role = "rahbariyat"
        staff.university_id = 1
        
        from api.management import get_mgmt_documents_archive
        
        print("\n--- Testing Archive (Hammasi) ---")
        res = await get_mgmt_documents_archive(
            title=None,
            staff=staff,
            db=db
        )
        print(f"Success: {res['success']}")
        print(f"Total Count: {res['total_count']}")
        print(f"Items: {len(res['data'])}")
        for i, d in enumerate(res['data'][:5]):
            is_cert = d.get('is_certificate', False)
            print(f"  {i+1}. Title='{d['title']}', Cert={is_cert}, Student='{d['student']['full_name']}'")

        print("\n--- Testing Archive (Sertifikatlar Only) ---")
        res_cert = await get_mgmt_documents_archive(
            title="Sertifikatlar",
            staff=staff,
            db=db
        )
        print(f"Success: {res_cert['success']}")
        print(f"Total Count: {res_cert['total_count']}")
        print(f"Items: {len(res_cert['data'])}")

if __name__ == "__main__":
    asyncio.run(main())

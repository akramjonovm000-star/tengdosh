import asyncio
import sys
import json
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff
from sqlalchemy import select
from api.management import search_mgmt_students
from services.hemis_service import HemisService

async def main():
    async with AsyncSessionLocal() as db:
        staff_stmt = select(Staff).where(Staff.role == 'rahbariyat').limit(1)
        staff_res = await db.execute(staff_stmt)
        staff = staff_res.scalar_one_or_none()
        
        if not staff:
            print("No staff found for testing")
            return

        query = "395251101397"
        
        # We need to see what HemisService actually gets
        from config import HEMIS_ADMIN_TOKEN
        filters = {"search": query}
        items, total = await HemisService.get_admin_student_list(filters, page=1, limit=1)
        
        if items:
            print("RAW HEMIS ITEM KEYS:", items[0].keys())
            print("RAW HEMIS ITEM DATA:", json.dumps(items[0], indent=2, ensure_ascii=False))
            
            # Now test the search_mgmt_students result
            result = await search_mgmt_students(
                query=query,
                staff=staff,
                db=db
            )
            
            if result['success'] and result['data']:
                found = result['data'][0]
                print(f"\nFinal Mapped Result ID: {found['id']}")
                print(f"Final Mapped Result Login: {found['hemis_login']}")
        else:
            print("No students found in HEMIS API for query.")

if __name__ == "__main__":
    asyncio.run(main())

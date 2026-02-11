import asyncio
import sys
import json
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff
from sqlalchemy import select
from api.management import get_mgmt_student_details

async def main():
    async with AsyncSessionLocal() as db:
        # Get a real staff for context
        staff_stmt = select(Staff).where(Staff.role == 'rahbariyat').limit(1)
        staff_res = await db.execute(staff_stmt)
        staff = staff_res.scalar_one_or_none()
        
        if not staff:
            print("No staff found for testing")
            return

        # Test with Student ID 730 (Rahimxonov)
        student_id = 730
        try:
            print(f"Testing full-details for student_id: {student_id}")
            result = await get_mgmt_student_details(
                student_id=student_id,
                staff=staff,
                db=db
            )
            print("Response success:", result.get("success"))
            if result.get("success"):
                print("Profile name:", result['data']['profile']['full_name'])
                print("Appeals count:", len(result['data']['appeals']))
            else:
                print("Response failed:", result)
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

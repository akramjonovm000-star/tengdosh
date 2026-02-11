import asyncio
import sys
import json
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select
from api.management import get_mgmt_analytics

async def main():
    async with AsyncSessionLocal() as db:
        # Get a real staff for context
        staff_stmt = select(Staff).where(Staff.role == 'rahbariyat').limit(1)
        staff_res = await db.execute(staff_stmt)
        staff = staff_res.scalar_one_or_none()
        
        if not staff:
            print("No staff found for testing")
            return

        try:
            print("Testing management/analytics...")
            result = await get_mgmt_analytics(
                staff=staff,
                db=db
            )
            print("Response success:", result.get("success"))
            if result.get("success"):
                print("DATA KEYS:", result['data'].keys())
                # print(json.dumps(result['data'], indent=2, ensure_ascii=False))
            else:
                print("Response failed:", result)
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

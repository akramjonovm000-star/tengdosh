import asyncio
import os
import sys
import logging

# Add project root
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.ERROR) # Only show errors by default

from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select, or_
from api.management_appeals import get_appeals_list, get_appeals_stats
import json

async def mock_call_appeals(staff, db):
    try:
        hemis_role = getattr(staff, 'hemis_role', "N/A")
        print(f"Testing {staff.full_name} (ID: {staff.id}, Role: {staff.role}, HEMIS: {hemis_role}, Fac: {staff.faculty_id})...")
        
        # Test List
        result_list = await get_appeals_list(page=1, limit=1, staff=staff, db=db)
        print(f"  [LIST] SUCCESS. Got {len(result_list)} items.")
        
        # Verify JSON
        try:
            json.dumps(result_list, default=str)
        except Exception as e:
            print(f"  [LIST] JSON ERROR: {e}")

        # Test Stats
        result_stats = await get_appeals_stats(staff=staff, db=db)
        print(f"  [STATS] SUCCESS. Data: {str(result_stats)[:50]}...")
        
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()

async def test_all_staff():
    async with AsyncSessionLocal() as db:
        # Get all potentially relevant staff
        stmt = select(Staff)
        staff_list = (await db.execute(stmt)).scalars().all()
        
        print(f"Checking {len(staff_list)} staff members...")
        
        count = 0
        for s in staff_list:
            # Check only likely management roles to save time
            hemis_role = getattr(s, 'hemis_role', None)
            if s.role in ['rahbariyat', 'dekan', 'dekan_orinbosari', 'admin', 'owner', 'rektor', 'prorektor'] or hemis_role == 'rahbariyat':
                await mock_call_appeals(s, db)
                count += 1
                
        print(f"Tested {count} staff members.")

if __name__ == "__main__":
    asyncio.run(test_all_staff())

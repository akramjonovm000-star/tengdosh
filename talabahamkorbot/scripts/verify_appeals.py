
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

from api.management_appeals import get_appeals_stats

async def run():
    async with AsyncSessionLocal() as session:
        print("--- Verifying Appeals Analytics ---")
        
        # 1. Mock Staff (Owner/Admin)
        stmt = select(Staff).where(Staff.role == 'owner', Staff.university_id != None).limit(1)
        staff = (await session.execute(stmt)).scalar()
        if not staff:
            # Fallback to any admin
            stmt = select(Staff).where(Staff.role.in_(['rahbariyat', 'rektor', 'prorektor']), Staff.university_id != None).limit(1)
            staff = (await session.execute(stmt)).scalar()
            
        if not staff:
            print("No suitable admin staff found for testing.")
            return

        print(f"Testing as Staff: {staff.full_name} (Role: {staff.role}, Uni ID: {staff.university_id})")
        
        # 2. Get Stats
        print("\nFetching Appeals Stats...")
        try:
            stats = await get_appeals_stats(staff=staff, db=session)
            
            print(f"Total Active: {stats['total_active']}")
            print(f"Total Resolved: {stats['total_resolved']}")
            print(f"Total Overdue: {stats['total_overdue']}")
            
            print("\nFaculty Performance:")
            for fp in stats['faculty_performance']:
                print(f" - {fp['faculty']}: Total={fp['total']}, Overdue={fp['overdue']}, AvgTime={fp['avg_response_time']}h")
                if fp['topics']:
                    print(f"   Topics: {fp['topics']}")
                    
            print("\nTop Targets:")
            for t in stats['top_targets']:
                print(f" - {t['role']}: {t['count']}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())

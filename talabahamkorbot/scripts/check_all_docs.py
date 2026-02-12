import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import ActivityLog, ActivityType, Student

async def check_all_docs():
    async with AsyncSessionLocal() as db:
        print("Checking for ALL Uploaded Documents (Global Stats)...")
        
        # 1. Check Activity Logs (Certificates/Documents)
        target_types = ['certificate', 'document']
        
        stmt = select(ActivityLog.activity_type, func.count(ActivityLog.id))\
            .where(ActivityLog.activity_type.in_(target_types))\
            .group_by(ActivityLog.activity_type)
            
        logs = (await db.execute(stmt)).all()
        
        print("\n--- Activity Log Check (Global) ---")
        total_docs = 0
        if logs:
            for type_, count in logs:
                print(f"- {type_}: {count} uploaded")
                total_docs += count
        else:
            print("No 'certificate' or 'document' activities found in the entire database.")
            
        print(f"TOTAL UPLOADS: {total_docs}")

        # 2. Check Students with Images (Just for context)
        stmt = select(func.count(Student.id)).where(Student.image_url != None)
        total_images = (await db.execute(stmt)).scalar()
        print(f"\n--- Profile Images (Global) ---")
        print(f"Total students with image_url (likely profile pics): {total_images}")

if __name__ == "__main__":
    asyncio.run(check_all_docs())

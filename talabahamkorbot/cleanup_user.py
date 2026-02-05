import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TgAccount, StaffRole

async def cleanup():
    async with AsyncSessionLocal() as s:
        print("Cleaning up User ID: 7476703866")
        
        # 1. Fetch all staff records for this TG ID
        r = await s.execute(select(Staff).where(Staff.telegram_id == 7476703866))
        staff_records = r.scalars().all()
        
        if len(staff_records) > 1:
            # Sort by ID or Role. We want the one with 'developer' role to be active (ID 27)
            # and the 'owner' one (ID 24) to be deactivated or role changed.
            for dev in staff_records:
                if dev.role == "owner" and dev.id == 24:
                    print(f"Deactivating legacy owner record ID={dev.id}")
                    dev.is_active = False
                    dev.telegram_id = None # Remove TG ID to avoid future conflicts
                elif dev.role == "developer":
                    print(f"Ensuring developer record ID={dev.id} is active")
                    dev.is_active = True
            
            await s.commit()
            print("Cleanup committed.")
        else:
            print("No duplicates found, nothing to clean.")

if __name__ == "__main__":
    asyncio.run(cleanup())

import asyncio
import os
import sys
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Banner

async def main():
    print("Checking banners...")
    async with AsyncSessionLocal() as session:
        # Fetch all banners
        result = await session.execute(select(Banner))
        banners = result.scalars().all()
        
        if not banners:
            print("No banners found in database.")
            return

        print(f"Found {len(banners)} banners.")
        
        count = 0
        for b in banners:
            if count < 2:
                if not b.is_active:
                    b.is_active = True
                    print(f"Activating Banner ID: {b.id}")
                else:
                    print(f"Banner ID: {b.id} is already active.")
                count += 1
            else:
                # Optional: Deactivate others if strict "two banners" is needed
                # But user said "activate two", not "only two". 
                # Let's keep it safe and just ensure first two are active.
                pass
        
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import SubscriptionPlan
from sqlalchemy import select

async def main():
    plans = [
        {"name": "Bir oylik", "duration_days": 30, "price_uzs": 10000},
        {"name": "Uch oylik", "duration_days": 90, "price_uzs": 25000},
        {"name": "Olti oylik", "duration_days": 180, "price_uzs": 40000},
        {"name": "Bir yillik", "duration_days": 365, "price_uzs": 70000},
    ]
    
    async with AsyncSessionLocal() as session:
        for p in plans:
            # Check if exists
            stmt = select(SubscriptionPlan).where(SubscriptionPlan.duration_days == p["duration_days"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                new_plan = SubscriptionPlan(**p)
                session.add(new_plan)
                print(f"Added plan: {p['name']}")
            else:
                existing.name = p["name"]
                existing.price_uzs = p["price_uzs"]
                print(f"Updated plan: {p['name']}")
        
        await session.commit()
    print("Seeding finished.")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import SubscriptionPlan

async def list_plans():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SubscriptionPlan))
        plans = result.scalars().all()
        print(f"Total Plans: {len(plans)}")
        for p in plans:
            print(f"ID: {p.id}, Name: '{p.name}', Duration: {p.duration_days}, Price: {p.price_uzs}")

if __name__ == "__main__":
    asyncio.run(list_plans())

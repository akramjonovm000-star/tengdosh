import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity

async def fix_statuses():
    async with AsyncSessionLocal() as db:
        # Update accepted to approved
        stmt1 = update(UserActivity).where(UserActivity.status == 'accepted').values(status='approved')
        res1 = await db.execute(stmt1)
        
        # Update confirmed to approved
        stmt2 = update(UserActivity).where(UserActivity.status == 'confirmed').values(status='approved')
        res2 = await db.execute(stmt2)
        
        await db.commit()
        print(f"Updated accepted -> approved: {res1.rowcount}")
        print(f"Updated confirmed -> approved: {res2.rowcount}")

asyncio.run(fix_statuses())

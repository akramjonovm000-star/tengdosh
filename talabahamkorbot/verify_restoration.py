import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity, UserActivityImage

async def main():
    async with AsyncSessionLocal() as session:
        # Check activities for student 729
        stmt = select(UserActivity).where(UserActivity.student_id == 729)
        result = await session.execute(stmt)
        acts = result.scalars().all()
        
        print(f"--- Student 729 Activities ({len(acts)}) ---")
        for a in acts:
            # check images count
            img_stmt = select(UserActivityImage).where(UserActivityImage.activity_id == a.id)
            img_res = await session.execute(img_stmt)
            imgs = img_res.scalars().all()
            print(f"[{a.id}] {a.name} | Status: {a.status} | Images: {len(imgs)} | Created: {a.created_at}")

        # Check total activities in DB
        total_stmt = select(UserActivity)
        total_res = await session.execute(total_stmt)
        total_acts = total_res.scalars().all()
        print(f"\nTotal Activities in DB: {len(total_acts)}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from sqlalchemy import select, and_
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity

async def main():
    async with AsyncSessionLocal() as session:
        print("--- Checking for Activities in Gap (46-484) ---")
        stmt = select(UserActivity).where(and_(UserActivity.id > 45, UserActivity.id < 484))
        result = await session.execute(stmt)
        items = result.scalars().all()
        print(f"Found {len(items)} activities in this range.")
        for i in items:
            print(f"- [{i.id}] {i.name} (Student: {i.student_id}) | Created: {i.created_at}")

        # check for any other tables? no just this.
if __name__ == "__main__":
    asyncio.run(main())

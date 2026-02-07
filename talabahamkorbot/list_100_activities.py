import asyncio
from sqlalchemy import select, desc
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity

async def main():
    async with AsyncSessionLocal() as session:
        print("--- Last 100 Activities ---")
        stmt = (
            select(UserActivity, Student.full_name)
            .join(Student, UserActivity.student_id == Student.id)
            .order_by(desc(UserActivity.id))
            .limit(100)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for act, s_name in rows:
            print(f"[{act.id}] {s_name} (ID: {act.student_id}) | Name: {act.name} | Status: {act.status} | Created: {act.created_at}")

        # Check for gaps
        stmt_max = select(UserActivity.id).order_by(desc(UserActivity.id)).limit(1)
        max_id = await session.execute(stmt_max)
        max_id = max_id.scalar()
        print(f"\nMax Activity ID: {max_id}")
        
        stmt_all_ids = select(UserActivity.id).order_by(desc(UserActivity.id))
        all_ids = (await session.execute(stmt_all_ids)).scalars().all()
        print(f"Total entries: {len(all_ids)}")

if __name__ == "__main__":
    asyncio.run(main())

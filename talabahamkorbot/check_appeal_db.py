import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import StudentFeedback

async def check_stats():
    async with AsyncSessionLocal() as db:
        stmt = select(StudentFeedback.status, func.count(StudentFeedback.id))\
            .where(StudentFeedback.parent_id == None)\
            .group_by(StudentFeedback.status)
        rows = (await db.execute(stmt)).all()
        
        print("Root Appeal Status Counts:")
        for status, count in rows:
            print(f"  {status}: {count}")

        # Check a few samples
        stmt_sample = select(StudentFeedback).where(StudentFeedback.status == 'resolved').limit(5)
        resolved_samples = (await db.execute(stmt_sample)).scalars().all()
        print(f"\nSample 'resolved' appeals: {len(resolved_samples)}")
        for r in resolved_samples:
            print(f"  ID: {r.id}, StudentID: {r.student_id}, Text: {r.text[:30]}...")

if __name__ == "__main__":
    asyncio.run(check_stats())

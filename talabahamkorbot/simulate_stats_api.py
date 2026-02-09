import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentFeedback
from api.schemas import AppealStatsSchema

async def simulate_api():
    async with AsyncSessionLocal() as db:
        # Get a student who has appeals (e.g. 730)
        student_id = 730
        
        stmt = select(StudentFeedback).where(
            StudentFeedback.student_id == student_id,
            StudentFeedback.parent_id == None
        )
        result = await db.execute(stmt)
        results = result.scalars().all()
        
        answered_statuses = ['answered', 'resolved', 'replied']
        
        pending_count = len([f for f in results if f.status not in answered_statuses + ['closed', 'rejected']])
        answered_count = len([f for f in results if f.status in answered_statuses])
        closed_count = len([f for f in results if f.status == 'closed'])
        
        stats = AppealStatsSchema(
            pending=pending_count,
            answered=answered_count,
            closed=closed_count
        )
        
        print(f"Stats for student {student_id}:")
        print(f"  Total root appeals: {len(results)}")
        print(f"  Pending: {stats.pending}")
        print(f"  Answered: {stats.answered}")
        print(f"  Closed: {stats.closed}")
        
        print("\nStatuses found:")
        for f in results:
            print(f"  ID {f.id}: {f.status}")

if __name__ == "__main__":
    asyncio.run(simulate_api())

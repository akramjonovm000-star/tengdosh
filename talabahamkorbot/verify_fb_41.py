import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import StudentFeedback

async def verify_status():
    async with AsyncSessionLocal() as db:
        stmt = select(StudentFeedback).where(StudentFeedback.id == 41)
        fb = await db.scalar(stmt)
        if fb:
            print(f"Appeal ID 41 Status in DB: '{fb.status}'")
            # Simulate mapping logic from get_my_feedback
            status_for_json = fb.status
            print(f"Status for JSON: '{status_for_json}'")
        else:
            print("Appeal ID 41 not found")

if __name__ == "__main__":
    asyncio.run(verify_status())

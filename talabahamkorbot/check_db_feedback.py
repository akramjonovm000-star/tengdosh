
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import StudentFeedback
from sqlalchemy import select, desc

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(StudentFeedback).order_by(desc(StudentFeedback.id)).limit(10))
        rows = res.scalars().all()
        if not rows:
            print("No feedback found in database.")
            return
        for row in rows:
            print(f"ID: {row.id} | Student: {row.student_id} | Text: {row.text[:30]} | Status: {row.status} | Anonymous: {row.is_anonymous} | Date: {row.created_at}")

if __name__ == "__main__":
    asyncio.run(check())

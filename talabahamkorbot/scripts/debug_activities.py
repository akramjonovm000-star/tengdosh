import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity, Faculty

async def debug_activities():
    async with AsyncSessionLocal() as db:
        stmt = (
            select(UserActivity, Student.faculty_id, Student.university_id)
            .join(Student, UserActivity.student_id == Student.id)
            .limit(20)
        )
        res = await db.execute(stmt)
        rows = res.all()
        
        print(f"Total activities joined with students: {len(rows)}")
        for act, f_id, u_id in rows:
            print(f"ActID: {act.id}, StudentID: {act.student_id}, FacultyID: {f_id}, UniID: {u_id}")

        # Check total count for Faculty 34
        count_stmt = (
            select(UserActivity)
            .join(Student, UserActivity.student_id == Student.id)
            .where(Student.faculty_id == 34)
        )
        count_res = await db.execute(count_stmt)
        count_list = count_res.scalars().all()
        print(f"\nActivities for Faculty 34: {len(count_list)}")

if __name__ == "__main__":
    asyncio.run(debug_activities())

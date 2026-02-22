import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import UserActivity, Student

async def count_activities():
    async with AsyncSessionLocal() as db:
        stmt = (
            select(UserActivity.status, func.count(UserActivity.id))
            .select_from(UserActivity)
            .join(Student, UserActivity.student_id == Student.id)
            .where(Student.hemis_login.notlike('demo%'))
            .group_by(UserActivity.status)
        )
        result = await db.execute(stmt)
        for row in result.all():
            print(f"{row[0]}: {row[1]}")

asyncio.run(count_activities())

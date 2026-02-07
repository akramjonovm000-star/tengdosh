
import asyncio
from sqlalchemy import select, func, desc
from database.db_connect import AsyncSessionLocal
from database.models import User, Student

async def check_data():
    async with AsyncSessionLocal() as session:
        print("--- USER TABLE STATS ---")
        user_res = await session.execute(
            select(User.faculty_name, func.count(User.id).label('cnt'))
            .group_by(User.faculty_name)
            .order_by(desc('cnt'))
        )
        for row in user_res:
            print(f"User Faculty: '{row.faculty_name}' - Count: {row.cnt}")

        print("\n--- STUDENT TABLE STATS ---")
        stud_res = await session.execute(
            select(Student.faculty_name, func.count(Student.id).label('cnt'))
            .group_by(Student.faculty_name)
            .order_by(desc('cnt'))
        )
        for row in stud_res:
            print(f"Student Faculty: '{row.faculty_name}' - Count: {row.cnt}")

if __name__ == "__main__":
    asyncio.run(check_data())

import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_user():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Student).where(Student.username == 'javoh'))
        student = result.scalar_one_or_none()
        if student:
            print(f"FOUND: ID={student.id}, Name={student.full_name}, Username={student.username}")
        else:
            print("NOT FOUND")
        
        # Check total usernames
        result_all = await session.execute(select(Student).where(Student.username.is_not(None)))
        all_users = result_all.scalars().all()
        print(f"Total users with username: {len(all_users)}")
        for u in all_users:
             print(f"- {u.username} ({u.full_name})")

if __name__ == "__main__":
    asyncio.run(check_user())

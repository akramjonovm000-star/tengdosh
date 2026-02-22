import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import User, Student

async def check():
    async with AsyncSessionLocal() as db:
        users_count = await db.scalar(select(func.count(User.id)))
        students_count = await db.scalar(select(func.count(Student.id)))
        
        print(f"Total rows in 'users' table: {users_count}")
        print(f"Total rows in 'students' table: {students_count}")
        
        # also let's look at hemis_id type, or any other field that might only be set on login.
        # auth.py sets student.last_active_at, but we know there was a bug where it wasn't.
        # auth.py ALSO syncs to Users table.
        # IF tutor_sync.py ONLY writes to Student table, then the User table would contain ONLY those who actually logged in via auth.py or oauth.py!
        
        # Check tutor_sync.py logic or just look at users table count vs students
        users_in_students = await db.execute(select(User.hemis_login).limit(5))
        print("Some user hemis_logins:", users_in_students.scalars().all())

if __name__ == '__main__':
    asyncio.run(check())

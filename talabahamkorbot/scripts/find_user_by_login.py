
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff, User

async def find(login):
    async with AsyncSessionLocal() as s:
        print(f"🔍 Searching for login/id: {login}")
        
        # Search Student
        res = await s.execute(select(Student.hemis_id, Student.full_name, Student.hemis_login).where(Student.hemis_login == login))
        students = res.all()
        print('Student matches:', students)
        
        # Search User
        res = await s.execute(select(User.hemis_id, User.full_name, User.hemis_login).where(User.hemis_login == login))
        users = res.all()
        print('User matches:', users)
        
        # Search Staff
        res = await s.execute(select(Staff.hemis_id, Staff.full_name).where(Staff.full_name.ilike(f"%{login}%")))
        staff = res.all()
        print('Staff name matches:', staff)

if __name__ == "__main__":
    import sys
    asyncio.run(find(sys.argv[1]))

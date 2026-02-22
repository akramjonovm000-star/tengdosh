import asyncio
import json
from sqlalchemy import select, func, or_
from database.db_connect import get_db
from database.models import Student, Staff, TgAccount, StaffRole

async def check_user_activity():
    async for db in get_db():
        # Check total students
        total = await db.scalar(select(func.count(Student.id)))
        
        # Check how many have hemis_token
        with_token = await db.scalar(select(func.count(Student.id)).where(Student.hemis_token != None))
        
        # Check how many have hemis_password
        with_password = await db.scalar(select(func.count(Student.id)).where(Student.hemis_password != None))
        
        # Check how many have username
        with_username = await db.scalar(select(func.count(Student.id)).where(Student.username != None))
        
        # Check how many have phone
        with_phone = await db.scalar(select(func.count(Student.id)).where(Student.phone != None))
        
        print(f"Total: {total}")
        print(f"With token: {with_token}")
        print(f"With password: {with_password}")
        print(f"With username: {with_username}")
        print(f"With phone: {with_phone}")

if __name__ == '__main__':
    asyncio.run(check_user_activity())

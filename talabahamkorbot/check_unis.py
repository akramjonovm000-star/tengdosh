import asyncio
import json
from sqlalchemy import select, func, or_
from database.db_connect import get_db
from database.models import Student, Staff, TgAccount, StaffRole, University

async def check_unis():
    async for db in get_db():
        # Check universities
        unis = await db.execute(select(University))
        print("Universities:")
        for u in unis.scalars().all():
            count = await db.scalar(select(func.count(Student.id)).where(Student.university_id == u.id))
            print(f"  ID: {u.id}, Code: {u.uni_code}, Name: {u.name}, Students: {count}")
            
        # Also check students without university
        no_uni_count = await db.scalar(select(func.count(Student.id)).where(Student.university_id == None))
        print(f"Students without university: {no_uni_count}")

if __name__ == '__main__':
    asyncio.run(check_unis())

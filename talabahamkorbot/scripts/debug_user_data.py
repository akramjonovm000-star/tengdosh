import asyncio
import os
import sys
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import User, Student

async def main():
    print("Analyzing User vs Student data...")
    async with AsyncSessionLocal() as session:
        # Check users with missing faculty
        query = (
            select(User.hemis_login, User.full_name, User.faculty_name, Student.faculty_name.label("student_faculty"))
            .outerjoin(Student, User.hemis_login == Student.hemis_login)
            .where(User.role == 'student')
            .where((User.faculty_name == None) | (User.faculty_name == ''))
            .limit(20)
        )
        
        result = await session.execute(query)
        rows = result.all()
        
        print(f"Found {len(rows)} users with missing User.faculty_name (Sample 20):")
        for r in rows:
            print(f"Login: {r.hemis_login}, Name: {r.full_name}")
            print(f"  User.Faculty: {r.faculty_name}")
            print(f"  Student.Faculty: {r.student_faculty}")
            print("-" * 20)
            
        # Count stats
        total_users = await session.scalar(select(func.count(User.id)).where(User.role == 'student'))
        missing_user_fac = await session.scalar(select(func.count(User.id)).where(User.role == 'student', (User.faculty_name == None) | (User.faculty_name == '')))
        
        # Check how many of missing have student data
        recoverable = await session.scalar(
            select(func.count(User.id))
            .outerjoin(Student, User.hemis_login == Student.hemis_login)
            .where(User.role == 'student')
            .where((User.faculty_name == None) | (User.faculty_name == ''))
            .where(Student.faculty_name != None)
        )
        
        print(f"\nStats:")
        print(f"Total Students in User table: {total_users}")
        print(f"Missing Faculty in User table: {missing_user_fac}")
        print(f"Recoverable from Student table: {recoverable}")

from sqlalchemy import func

if __name__ == "__main__":
    asyncio.run(main())

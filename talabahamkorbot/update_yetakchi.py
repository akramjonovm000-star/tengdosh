import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import User, Student, University

async def main():
    async with AsyncSessionLocal() as db:
        # First, query the university to see if it exists
        uni_query = await db.scalars(select(University).filter(University.name.ilike('%jurnalistika%')))
        uni = uni_query.first()
        if uni:
            print(f"Found university: {uni.name} (ID: {uni.id})")
        else:
            print("University not found using 'jurnalistika'. Creating a dummy or will use name mapping.")
        
        # Check if login exists
        login = '395251101397'
        student = await db.scalar(select(Student).where(Student.hemis_login == login))
        if student:
            print(f"Found student: {student.full_name}, Current role: {student.hemis_role}, University Name: {student.university_name}")
            # Update role to yetakchi
            student.hemis_role = 'yetakchi'
            if uni:
                student.university_id = uni.id
                student.university_name = uni.name
            await db.commit()
            print("Successfully updated student to yetakchi.")
        else:
            print(f"Student with login {login} NOT FOUND in DB.")

if __name__ == '__main__':
    asyncio.run(main())

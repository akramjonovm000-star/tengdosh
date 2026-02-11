import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, Student, UserActivity, Faculty
import json

async def debug_data():
    async with AsyncSessionLocal() as db:
        # 1. Check Staff
        staff_res = await db.execute(select(Staff).limit(5))
        staff_list = staff_res.scalars().all()
        print("--- STAFF SAMPLES ---")
        for s in staff_list:
            print(f"ID: {s.id}, Name: {s.full_name}, Uni: {s.university_id}, Faculty: {s.faculty_id}, Role: {getattr(s, 'role', 'N/A')}")

        # 2. Check Students
        student_res = await db.execute(select(Student).limit(5))
        student_list = student_res.scalars().all()
        print("\n--- STUDENT SAMPLES ---")
        for s in student_list:
            print(f"ID: {s.id}, Name: {s.full_name}, Uni: {s.university_id}, Faculty: {s.faculty_id}")

        # 3. Check Activities
        activity_res = await db.execute(select(UserActivity).limit(5))
        activity_list = activity_res.scalars().all()
        print("\n--- ACTIVITY SAMPLES ---")
        for a in activity_list:
            print(f"ID: {a.id}, StudentID: {a.student_id}, Name: {a.name}")

        # 4. Check Faculties
        faculty_res = await db.execute(select(Faculty).limit(10))
        faculty_list = faculty_res.scalars().all()
        print("\n--- FACULTY SAMPLES ---")
        for f in faculty_list:
            print(f"ID: {f.id}, Name: {f.name}, Uni: {f.university_id}")

if __name__ == "__main__":
    asyncio.run(debug_data())

import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff, Student
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        print("--- STUDENTS ---")
        students = await db.execute(select(Student).where(Student.hemis_login.ilike('demo%')))
        for s in students.scalars():
            print(f"Student: id={s.id} login={s.hemis_login} name={s.full_name} role={s.hemis_role} uni={s.university_id} fac={s.faculty_id}")

        print("--- STAFF ---")
        staffs = await db.execute(select(Staff).where(Staff.hemis_login.ilike('demo%')))
        for s in staffs.scalars():
            print(f"Staff: id={s.id} login={s.hemis_login} name={s.full_name} role={s.role} uni={s.university_id} fac={s.faculty_id}")

asyncio.run(main())

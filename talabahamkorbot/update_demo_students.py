import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff, Student
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        print("--- UPDATING DEMO STUDENTS ---")
        students = await db.execute(select(Student).where(Student.hemis_login.ilike('%demo%')))
        for s in students.scalars():
            s.university_id = 1
            print(f"Updated Student: id={s.id} login={s.hemis_login} to uni=1")
        
        students2 = await db.execute(select(Student).where(Student.full_name.ilike('%sanjar%123%')))
        for s in students2.scalars():
             s.university_id = 1
             print(f"Updated Student: id={s.id} name={s.full_name} to uni=1")
             
        students3 = await db.execute(select(Student).where(Student.hemis_login == 'sanjar.123'))
        for s in students3.scalars():
             s.university_id = 1
             print(f"Updated Student: id={s.id} name={s.full_name} to uni=1")
             
        await db.commit()
    print("ALL DONE")

asyncio.run(main())

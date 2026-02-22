import asyncio
import json
from sqlalchemy import select, func, or_
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_group_users():
    async with AsyncSessionLocal() as db:
        stmt = select(Student).where(
            Student.university_id == 1,
            Student.group_number == "25-21",
            Student.last_active_at != None
        )
        
        # We can also be safe and use ILIKE '%25-21%' just in case it's written differently
        stmt_ilike = select(Student).where(
            Student.university_id == 1,
            Student.group_number.ilike("%25-21%"),
            Student.last_active_at != None
        )
        
        result_ilike = await db.execute(stmt_ilike)
        students = result_ilike.scalars().all()
        
        print("25-21 guruhidagi faol ilova foydalanuvchilari:")
        if not students:
            print("Ushbu guruhdan hech kim ilovaga kirmagan.")
        else:
            for i, s in enumerate(students, 1):
                faculty = s.faculty_name or "Nomalum fakultet"
                level = s.level_name or "Nomalum kurs"
                print(f"{i}. {s.full_name} | {s.group_number} | {level} | {faculty}")

if __name__ == '__main__':
    asyncio.run(check_group_users())

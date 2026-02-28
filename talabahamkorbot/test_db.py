import asyncio
from sqlalchemy import select
from database.db_connect import engine
from database.models import Staff, TutorGroup, Student

async def main():
    async with engine.begin() as conn:
        # Find a tutor
        res = await conn.execute(select(Staff).where(Staff.role == 'tutor').limit(1))
        tutor = res.first()
        if not tutor:
            print("No tutors found")
            return
            
        print(f"Tutor: {tutor.full_name}")
        
        # Get groups
        res2 = await conn.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor.id))
        groups = res2.all()
        print(f"Groups: {[g.group_number for g in groups]}")
        
        if groups:
            g = groups[0].group_number
            res3 = await conn.execute(select(Student).where(Student.group_number == g))
            students = res3.all()
            print(f"Students in {g}: {len(students)}")
            if students:
                s = students[0]
                print(f"First student: {s.full_name}, limit keys: id, image_url, group_number")

if __name__ == "__main__":
    asyncio.run(main())

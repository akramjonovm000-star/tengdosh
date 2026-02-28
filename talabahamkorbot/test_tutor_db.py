import asyncio
from sqlalchemy import select
from database.db_connect import engine
from database.models import Staff, TutorGroup, Student

async def main():
    async with engine.begin() as conn:
        res = await conn.execute(select(Staff).where(Staff.role == 'tutor').limit(1))
        tutor = res.first()
        res = await conn.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor.id))
        groups = res.all()
        for g in groups:
            print(f"[{g.group_number}]")
            res2 = await conn.execute(select(Student.group_number).where(Student.group_number.like(f"%{g.group_number[:2]}%")).distinct())
            student_groups = res2.all()
            print(f"   => Students with similar groups: {[x[0] for x in student_groups]}")
            
            res3 = await conn.execute(select(Student).where(Student.group_number == g.group_number))
            students = res3.all()
            print(f"   => Exact match count: {len(students)}")
            
if __name__ == "__main__":
    asyncio.run(main())

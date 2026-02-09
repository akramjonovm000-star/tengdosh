import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff

async def check_user():
    async with AsyncSessionLocal() as db:
        print("Checking Students...")
        stmt = select(Student).where(Student.username.ilike('%Sanjar%'))
        res = await db.execute(stmt)
        students = res.scalars().all()
        for s in students:
            print(f"Student: ID={s.id}, Username={s.username}, FullName={s.full_name}, HemisLogin={s.hemis_login}")
        
        print("\nChecking Staff...")
        stmt = select(Staff).where(Staff.username.ilike('%Sanjar%'))
        res = await db.execute(stmt)
        staff_members = res.scalars().all()
        for st in staff_members:
            print(f"Staff: ID={st.id}, Username={st.username}, FullName={st.full_name}, Role={st.role}")

        print("\nChecking for Demo users...")
        # Search by hemis_login if it's 'demo' or similar
        stmt = select(Student).where(Student.hemis_login.ilike('%demo%'))
        res = await db.execute(stmt)
        demo_students = res.scalars().all()
        for ds in demo_students:
            print(f"Demo Student: ID={ds.id}, Username={ds.username}, Login={ds.hemis_login}")

if __name__ == "__main__":
    asyncio.run(check_user())

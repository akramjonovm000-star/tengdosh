import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text, select
from database.db_connect import engine, AsyncSessionLocal
from database.models import Student, TutorGroup, Base

async def sync_groups():
    async with AsyncSessionLocal() as session:
        # 1. Update hyphens in students table
        print("Normalizing group numbers (replacing '-' with '–')...")
        await session.execute(text("UPDATE students SET group_number = REPLACE(group_number, '-', '–') WHERE group_number LIKE '%-%'"))
        await session.commit()
        
        # 2. Get unique groups from students
        print("Fetching unique groups from students...")
        stmt = select(
            Student.group_number, 
            Student.faculty_id, 
            Student.university_id
        ).where(
            Student.group_number.is_not(None)
        ).distinct()
        
        result = await session.execute(stmt)
        student_groups = result.all()
        
        # 3. Insert into tutor_groups if not exists
        count = 0
        for gr_num, fac_id, uni_id in student_groups:
            # Check if exists
            exists = await session.scalar(
                select(TutorGroup).where(TutorGroup.group_number == gr_num)
            )
            if not exists:
                new_group = TutorGroup(
                    group_number=gr_num,
                    faculty_id=fac_id,
                    university_id=uni_id,
                    tutor_id=None # Initially no tutor
                )
                session.add(new_group)
                count += 1
        
        await session.commit()
        print(f"Synced {count} new groups.")

async def migrate_schema():
    # Re-create tutor_groups to apply nullable change
    async with engine.begin() as conn:
        print("Re-creating tutor_groups table for schema update...")
        await conn.execute(text("DROP TABLE IF EXISTS tutor_groups CASCADE"))
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await migrate_schema()
    await sync_groups()

if __name__ == "__main__":
    asyncio.run(main())

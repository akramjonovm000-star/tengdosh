import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import TutorGroup, Faculty

async def check_groups():
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count(TutorGroup.id)))
        print(f"Total TutorGroups: {count}")
        
        groups = await session.scalars(select(TutorGroup).limit(5))
        for g in groups:
            print(f"Group: {g.name}, FacultyID: {g.faculty_id}, TutorID: {g.tutor_id}")

        faculties = await session.scalars(select(Faculty))
        for f in faculties:
            g_count = await session.scalar(select(func.count(TutorGroup.id)).where(TutorGroup.faculty_id == f.id))
            print(f"Faculty: {f.name} (ID: {f.id}) -> Groups: {g_count}")

if __name__ == "__main__":
    asyncio.run(check_groups())

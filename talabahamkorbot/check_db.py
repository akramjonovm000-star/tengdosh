
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, Student

async def check():
    async with AsyncSessionLocal() as session:
        # Check Posts
        result = await session.execute(select(ChoyxonaPost))
        posts = result.scalars().all()
        print(f"Total Posts: {len(posts)}")
        for p in posts:
            print(f"ID: {p.id}, Content: {p.content}, Type: {p.category_type}, TargetUni: {p.target_university_id}, TargetFac: {p.target_faculty_id}")

        # Check Students (Just to see if we have valid university_ids)
        result_s = await session.execute(select(Student).limit(5))
        students = result_s.scalars().all()
        print("\n--- Students Sample ---")
        for s in students:
            print(f"ID: {s.id}, Name: {s.full_name}, UniID: {s.university_id}, FacID: {s.faculty_id}")

if __name__ == "__main__":
    asyncio.run(check())

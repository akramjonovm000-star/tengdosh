import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as session:
        ids = [729, 730, 756, 748]
        print(f"--- Checking Students {ids} ---")
        stmt = select(Student).where(Student.id.in_(ids))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        found_ids = {s.id for s in students}
        for s_id in ids:
            if s_id in found_ids:
                s = next(st for st in students if st.id == s_id)
                print(f"Student {s_id}: {s.full_name}")
            else:
                print(f"Student {s_id}: NOT FOUND")

if __name__ == "__main__":
    asyncio.run(main())

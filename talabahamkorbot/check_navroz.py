from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select
import asyncio

async def main():
    async with AsyncSessionLocal() as session:
        # Check specific names
        stmt = select(Student).where(Student.full_name.ilike("%Navro%"))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        print("--- Navro... ---")
        for s in students:
            print(f"ID: {s.id}, FullName: '{s.full_name}', ShortName: '{s.short_name}'")

        stmt = select(Student).where(Student.full_name.ilike("%G'Ofurov%"))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        print("\n--- G'Ofurov... ---")
        for s in students:
            print(f"ID: {s.id}, FullName: '{s.full_name}', ShortName: '{s.short_name}'")

if __name__ == "__main__":
    asyncio.run(main())

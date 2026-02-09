
import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    async with AsyncSessionLocal() as db:
        print("\n--- Student Fields Sample ---")
        stmt = select(Student).limit(5)
        result = await db.execute(stmt)
        students = result.scalars().all()
        for s in students:
            print(f"ID {s.id}: Level='{s.level_name}', EducationForm='{s.education_form}', Specialty='{s.specialty_name}'")

if __name__ == "__main__":
    asyncio.run(main())

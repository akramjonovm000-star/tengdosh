
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(Student.specialty_id, Student.specialty_name)
            .where(Student.specialty_name.ilike("%Dizayn%"))
            .limit(10)
        )
        rows = res.all()
        print("Dizayn related specialties in DB:")
        for sid, name in rows:
            print(f"  - {name}: ID {sid}")

if __name__ == "__main__":
    asyncio.run(main())

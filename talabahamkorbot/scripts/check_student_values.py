import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check_values():
    async with AsyncSessionLocal() as db:
        for field in ['education_type', 'education_form', 'level_name']:
            res = await db.execute(select(getattr(Student, field)).distinct())
            vals = [r[0] for r in res.all()]
            print(f"Distinct {field}: {vals}")

if __name__ == "__main__":
    asyncio.run(check_values())

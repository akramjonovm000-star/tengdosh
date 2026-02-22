import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def check():
    async with AsyncSessionLocal() as db:
        # check how many have static/uploads in image_url
        stmt1 = select(func.count(Student.id)).where(Student.image_url.ilike('%static/uploads%'))
        custom = await db.scalar(stmt1)
        
        stmt2 = select(func.count(Student.id)).where(
            Student.image_url.ilike('%static/uploads%'),
            Student.last_active_at == None
        )
        custom_no_active = await db.scalar(stmt2)
        
        print(f"Total with custom image (static/uploads): {custom}")
        print(f"Custom image but NO last_active_at: {custom_no_active}")
        
        # let's see some of them
        stmt3 = select(Student).where(
            Student.image_url.ilike('%static/uploads%'),
            Student.last_active_at == None,
            Student.university_id == 1,
            Student.group_number.ilike('%25-21%')
        )
        res = await db.execute(stmt3)
        for s in res.scalars().all():
            print(f"- {s.full_name}: {s.image_url}")

if __name__ == '__main__':
    asyncio.run(check())

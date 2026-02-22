import asyncio
from sqlalchemy import select, func, or_
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def final_stats():
    async with AsyncSessionLocal() as db:
        stmt = select(func.count(Student.id)).where(
            or_(
                Student.last_active_at != None,
                Student.image_url.ilike('%static/uploads%')
            )
        )
        total_active_all = await db.scalar(stmt)
        
        stmt2 = select(func.count(Student.id)).where(
            Student.university_id == 1,
            or_(
                Student.last_active_at != None,
                Student.image_url.ilike('%static/uploads%')
            )
        )
        total_active_jmcu = await db.scalar(stmt2)

        print(f"Barcha universitetlardagi faol: {total_active_all}")
        print(f"Faqat JMCU da faol: {total_active_jmcu}")

if __name__ == '__main__':
    asyncio.run(final_stats())

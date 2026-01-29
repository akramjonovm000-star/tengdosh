import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import StudentCache
from sqlalchemy import delete

async def clear_cache():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(StudentCache).where(StudentCache.key.like("subjects_%")))
        await session.execute(delete(StudentCache).where(StudentCache.key.like("attendance_%")))
        await session.commit()
        print("Subjects and Attendance cache cleared.")

if __name__ == "__main__":
    asyncio.run(clear_cache())

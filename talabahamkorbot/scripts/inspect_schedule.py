import asyncio
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import StudentCache, Student
from sqlalchemy import select

async def inspect():
    async with AsyncSessionLocal() as session:
        # Find any schedule cache
        stmt = select(StudentCache).where(StudentCache.key.like("schedule_%"))
        result = await session.execute(stmt)
        cache = result.scalars().first()
        
        if cache:
            print(f"Found cache for Student ID: {cache.student_id}")
            data = cache.data
            if isinstance(data, list) and len(data) > 0:
                print("--- Sample Lesson Item ---")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            else:
                print("Cache data is empty list")
        else:
             print("No schedule cache found. Please run /schedule command in bot first to populate cache.")

if __name__ == "__main__":
    asyncio.run(inspect())

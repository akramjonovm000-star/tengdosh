import asyncio
import sys
import os

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, distinct
from database.db_connect import create_async_engine, get_session_factory
from database.models import Student
from config import DATABASE_URL

async def list_faculties():
    # engine is already created in db_connect, no need to recreate if we import valid factory
    # But get_session_factory uses the global engine in db_connect
    AsyncSessionLocal = get_session_factory()
    
    async with AsyncSessionLocal() as session:
        stmt = select(distinct(Student.faculty_name)).where(Student.faculty_name.isnot(None))
        result = await session.execute(stmt)
        faculties = result.scalars().all()
        
        print("[-] Distinct Faculties in DB:")
        for f in faculties:
            print(f"    - '{f}'")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_faculties())

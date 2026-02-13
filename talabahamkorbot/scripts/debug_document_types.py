import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from config import DATABASE_URL
from database.models import StudentDocument

async def debug_types():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"--- Document Type Distribution ---")
        
        stmt = select(StudentDocument.file_type, func.count()).group_by(StudentDocument.file_type)
        res = await session.execute(stmt)
        types = res.all()
        
        for t, c in types:
            print(f"Type: '{t}' - Count: {c}")
            
        print(f"--- Document Name Check (for those with file_type='documents') ---")
        docs_stmt = select(StudentDocument.file_name).where(StudentDocument.file_type == 'document').limit(10)
        docs = (await session.execute(docs_stmt)).scalars().all()
        for d in docs:
            print(f"- {d}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_types())

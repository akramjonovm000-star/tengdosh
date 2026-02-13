import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from config import DATABASE_URL
from database.models import PendingUpload, StudentDocument

async def check_pending():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"--- Pending Uploads Check ---")
        try:
            pending_count = await session.scalar(select(func.count()).select_from(PendingUpload))
            print(f"Pending Uploads Count: {pending_count}")
        except Exception as e:
            print(f"PendingUpload table error: {e}")
            
        print(f"\n--- Inactive Documents Check ---")
        inactive_count = await session.scalar(select(func.count()).where(StudentDocument.is_active == False))
        print(f"Inactive Documents Count: {inactive_count}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_pending())

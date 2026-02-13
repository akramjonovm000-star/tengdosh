import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from config import DATABASE_URL
from database.models import UserDocument, StudentDocument

async def check_migration():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"--- Migration Check ---")
        
        # Check UserDocument (Legacy) Count
        try:
            legacy_count = await session.scalar(select(func.count()).select_from(UserDocument))
            print(f"Legacy UserDocument Count: {legacy_count}")
        except Exception as e:
            print(f"Legacy UserDocument table error or not found: {e}")
            legacy_count = 0
            
        # Check StudentDocument (New) Count
        new_count = await session.scalar(select(func.count()).select_from(StudentDocument))
        print(f"New StudentDocument Count: {new_count}")
        
        if legacy_count > 0:
            print("\n--- Identifying Missing Documents ---")
            # Get all legacy IDs
            legacy_ids = (await session.execute(select(UserDocument.id))).scalars().all()
            # If we migrated correctly, maybe we can match by file_id?
            # Or assume we just moved everything over?
            # Let's check by file_id
            
            stmt = select(UserDocument).limit(10)
            legacy_docs = (await session.execute(stmt)).scalars().all()
            for doc in legacy_docs:
                exists = await session.scalar(select(StudentDocument).where(StudentDocument.telegram_file_id == doc.file_id))
                status = "✅ Migrated" if exists else "❌ MISSING"
                print(f"Legacy ID: {doc.id} | Title: '{doc.title}' | Status: {status}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_migration())

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select, func, desc, text
from config import DATABASE_URL
from database.models import Student

async def debug_pending_details():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"--- Pending Uploads Details (Last 10) ---")
        
        # Use raw SQL to avoid model mismatch errors
        query = text("""
            SELECT p.session_id, p.category, p.title, p.file_ids, p.created_at, s.full_name 
            FROM pending_uploads p
            JOIN students s ON p.student_id = s.id
            ORDER BY p.created_at DESC
            LIMIT 10
        """)
        
        res = await session.execute(query)
        uploads = res.all()
        
        for up in uploads:
            # up is a tuple: (session_id, category, title, file_ids, created_at, full_name)
            file_ids = up[3][:20] + "..." if up[3] and len(up[3]) > 20 else up[3]
            print(f"Session: {up[0]} | Student: {up[5]} | Cat: '{up[1]}' | Title: '{up[2]}' | FileIDs: {file_ids} | Created: {up[4]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_pending_details())

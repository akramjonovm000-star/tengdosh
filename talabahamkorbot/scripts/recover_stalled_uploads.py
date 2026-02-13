import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, text
from config import DATABASE_URL
from database.models import PendingUpload, StudentDocument

async def recover_uploads():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print(f"--- Recovering Stalled Uploads (Robust) ---")
        
        # Use raw SQL to handle potentially missing columns (even though we added them)
        # Just to be safe, select relevant data
        query = text("""
            SELECT p.session_id, p.student_id, p.category, p.title, p.file_ids, p.created_at, 
                   p.file_unique_id, p.file_size, p.mime_type
            FROM pending_uploads p
            WHERE p.file_ids IS NOT NULL AND p.file_ids != ''
        """)
        
        res = await session.execute(query)
        rows = res.all()
        
        count = 0
        deleted_count = 0
        
        for row in rows:
            try:
                session_id, student_id, category, title, file_ids, created_at, f_unique, f_size, mime = row
                
                # Truncate title/category if needed
                if title and len(title) > 100: title = title[:100]
                if category and len(category) > 60: category = category[:60]
                
                # Handle comma separated file_ids
                if "," in file_ids:
                    first_id = file_ids.split(",")[0].strip()
                else:
                    first_id = file_ids.strip()
                
                if len(first_id) > 255: first_id = first_id[:255]

                # Construct a title
                final_title = title if title else (category if category else f"Recovered Upload {created_at.strftime('%Y-%m-%d')}")
                
                # Check for existing document with same FileUniqueId (if available)
                if f_unique:
                    exists = await session.execute(
                        select(StudentDocument).where(StudentDocument.telegram_file_unique_id == f_unique)
                    )
                    if exists.scalar():
                        print(f"Skipping duplicate unique_id: {f_unique}")
                        # Still delete from pending? Yes, duplicate.
                        await session.execute(text("DELETE FROM pending_uploads WHERE session_id = :sid"), {"sid": session_id})
                        deleted_count += 1
                        continue

                # Create new document
                new_doc = StudentDocument(
                    student_id=student_id,
                    telegram_file_id=first_id,
                    telegram_file_unique_id=f_unique,
                    file_name=final_title,
                    file_type="document",
                    mime_type=mime,
                    file_size=f_size,
                    uploaded_at=created_at,
                    uploaded_by="student",
                    is_active=True
                )
                session.add(new_doc)
                count += 1
                
                # Delete from pending
                # Use delete statement by session_id
                await session.execute(text("DELETE FROM pending_uploads WHERE session_id = :sid"), {"sid": session_id})
                deleted_count += 1
            except Exception as e:
                print(f"Error processing row {row[0]}: {e}")
            
        await session.commit()
        print(f"Recovered {count} documents from pending_uploads.")
        print(f"cleaned up {deleted_count} pending entries.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recover_uploads())

import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        # 1. Add columns to pending_uploads if they don't exist
        try:
            await session.execute(text("ALTER TABLE pending_uploads ADD COLUMN category VARCHAR(64);"))
            await session.execute(text("ALTER TABLE pending_uploads ADD COLUMN title VARCHAR(128);"))
            await session.commit()
            print("Migration successful: added category and title to pending_uploads")
        except Exception as e:
            await session.rollback()
            print(f"Migration error (already exists?): {e}")

        # 2. Delete the 'passport' document
        try:
            # First, check if it exists to be safe
            result = await session.execute(text("SELECT id FROM user_documents WHERE title = 'passport';"))
            doc_id = result.scalar()
            if doc_id:
                await session.execute(text(f"DELETE FROM user_documents WHERE id = {doc_id};"))
                await session.commit()
                print(f"Successfully deleted document ID {doc_id} ('passport')")
            else:
                print("Document 'passport' not found.")
        except Exception as e:
            await session.rollback()
            print(f"Error deleting document: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

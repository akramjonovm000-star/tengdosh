import asyncio
from sqlalchemy import text
from database.db_connect import engine
from database.models import Base

async def migrate():
    async with engine.begin() as conn:
        print("Checking for missing tables...")
        # multiple approaches, but simplest is let create_all handle new tables
        await conn.run_sync(Base.metadata.create_all)
        print("Ensured 'notifications' and other tables exist.")

        # Check if reply_to_user_id exists
        column_exists = False
        try:
             # Use a nested transaction or savepoint if possible, or just be careful.
             # In asyncpg/sqlalchemy, if a statement fails, the transaction is invalid.
             await conn.execute(text("SELECT reply_to_user_id FROM choyxona_comments LIMIT 1"))
             column_exists = True
             print("Column 'reply_to_user_id' already exists.")
        except Exception:
             print("Check failed (Column missing), preparing to add...")
        
        if not column_exists:
             # If previous query failed, we might need to rollback/restart logic if inside same transaction?
             # But 'conn.begin()' manages it. 
             # Actually, simpler way: Just catch the specific error and ignore, 
             # BUT since the trans is aborted, we can't run ALTER.
             # We should probably run these in separate connections for script simplicity.
             pass

    if not column_exists:
        # Re-connect for the ALTER to avoid Aborted Transaction state
        async with engine.begin() as conn2:
             print("Adding 'reply_to_user_id' column...")
             await conn2.execute(text("ALTER TABLE choyxona_comments ADD COLUMN reply_to_user_id INTEGER"))
             print("Column added.")

if __name__ == "__main__":
    asyncio.run(migrate())

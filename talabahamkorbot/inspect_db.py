
import asyncio
from sqlalchemy import select, func, inspect
from database.db_connect import AsyncSessionLocal, engine
from database.models import Student, TgAccount, StudentFeedback

async def inspect_db():
    async with AsyncSessionLocal() as session:
        pass # Not needed for now

    # 3. Check Schema
    print("\n--- StudentFeedback Schema Check ---")
    def check_cols(conn):
        cols = inspect(conn).get_columns("student_feedback")
        for c in cols:
            print(f"Col: {c['name']}, Type: {c['type']}")
    
    async with engine.connect() as conn:
        await conn.run_sync(check_cols)

if __name__ == "__main__":
    asyncio.run(inspect_db())

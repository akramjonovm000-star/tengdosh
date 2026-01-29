
import asyncio
from database.db_connect import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        await conn.execute(text("ALTER TABLE student_feedback ALTER COLUMN ai_topic TYPE VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE student_feedback ALTER COLUMN assigned_role TYPE VARCHAR(64)"))
        await conn.commit()
    print("✅ Schema updated")

if __name__ == "__main__":
    asyncio.run(main())

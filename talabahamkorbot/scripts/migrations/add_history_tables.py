import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def migrate():
    async with engine.begin() as conn:
        # 1. Add parent_id to student_feedback
        try:
            await conn.execute(text("ALTER TABLE student_feedback ADD COLUMN parent_id INTEGER REFERENCES student_feedback(id);"))
            print("Added parent_id column.")
        except Exception as e:
            print(f"parent_id migration error (maybe exists): {e}")

        # 2. Create feedback_replies table
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS feedback_replies (
                    id SERIAL PRIMARY KEY,
                    feedback_id INTEGER NOT NULL REFERENCES student_feedback(id) ON DELETE CASCADE,
                    staff_id INTEGER REFERENCES staff(id) ON DELETE SET NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
                );
            """))
            print("Created feedback_replies table.")
        except Exception as e:
            print(f"feedback_replies creation error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

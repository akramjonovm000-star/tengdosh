import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def add_ai_columns():
    async with engine.begin() as conn:
        # ai_topic
        await conn.execute(text("ALTER TABLE student_feedback ADD COLUMN IF NOT EXISTS ai_topic VARCHAR(64)"))
        # ai_sentiment
        await conn.execute(text("ALTER TABLE student_feedback ADD COLUMN IF NOT EXISTS ai_sentiment VARCHAR(32)"))
        # ai_summary
        await conn.execute(text("ALTER TABLE student_feedback ADD COLUMN IF NOT EXISTS ai_summary TEXT"))
        
        print("✅ Added ai_topic, ai_sentiment, ai_summary columns to student_feedback")

if __name__ == "__main__":
    asyncio.run(add_ai_columns())

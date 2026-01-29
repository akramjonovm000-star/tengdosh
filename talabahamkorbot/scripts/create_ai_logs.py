
import asyncio
from sqlalchemy import text
from database.db_connect import engine
from database.models import Base

async def create_log_table():
    async with engine.begin() as conn:
        try:
            # We use the Base metadata to create only the new table if possible,
            # but create_all usually checks for existence.
            # However, since we defined it in models.py which is imported by db_connect -> Base,
            # we can try running create_all for just this table or raw SQL.
            
            # Raw SQL is safer for single table addition without Alembic
            sql = """
            CREATE TABLE IF NOT EXISTS student_ai_logs (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                full_name VARCHAR(255),
                university_name VARCHAR(255),
                faculty_name VARCHAR(255),
                group_number VARCHAR(64),
                user_query TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
            );
            """
            await conn.execute(text(sql))
            print("Created student_ai_logs table")
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    asyncio.run(create_log_table())

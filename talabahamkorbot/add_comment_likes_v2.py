import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def migrate():
    # Use isolation_level="AUTOCOMMIT" to avoid transaction blocks on failure if possible,
    # or just separate executions.
    # checking engine 
    
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        
        print("1. Adding likes_count to choyxona_comments...")
        try:
            # Postgres supports IF NOT EXISTS for columns
            await conn.execute(text("ALTER TABLE choyxona_comments ADD COLUMN IF NOT EXISTS likes_count INTEGER DEFAULT 0"))
            print("Done.")
        except Exception as e:
            print(f"Error adding column: {e}")

        print("2. Creating choyxona_comment_likes table...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS choyxona_comment_likes (
                    id SERIAL PRIMARY KEY,
                    comment_id INTEGER NOT NULL REFERENCES choyxona_comments(id) ON DELETE CASCADE,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                    CONSTRAINT _user_comment_like_uc UNIQUE (comment_id, student_id)
                )
            """))
            print("Done.")
        except Exception as e:
             print(f"Error creating table: {e}")

        print("3. Backfilling counts...")
        try:
            await conn.execute(text("""
                UPDATE choyxona_comments c
                SET likes_count = (SELECT count(*) FROM choyxona_comment_likes l WHERE l.comment_id = c.id)
            """))
            print("Done.")
        except Exception as e:
            print(f"Error backfilling: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())

import asyncio
from sqlalchemy import text
from database.db_connect import engine
from database.models import Base

async def migrate():
    async with engine.begin() as conn:
        # 1. Add columns to choyxona_posts if they don't exist
        print("Checking/Adding columns to choyxona_posts...")
        try:
            await conn.execute(text("ALTER TABLE choyxona_posts ADD COLUMN likes_count INTEGER DEFAULT 0"))
            print("Added likes_count")
        except Exception as e:
            print(f"likes_count might already exist: {e}")

        try:
            await conn.execute(text("ALTER TABLE choyxona_posts ADD COLUMN comments_count INTEGER DEFAULT 0"))
            print("Added comments_count")
        except Exception as e:
            print(f"comments_count might already exist: {e}")

        try:
            await conn.execute(text("ALTER TABLE choyxona_posts ADD COLUMN reposts_count INTEGER DEFAULT 0"))
            print("Added reposts_count")
        except Exception as e:
            print(f"reposts_count might already exist: {e}")

        # 2. Create choyxona_post_reposts table
        print("Creating choyxona_post_reposts table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS choyxona_post_reposts (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL REFERENCES choyxona_posts(id) ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                CONSTRAINT _user_post_repost_uc UNIQUE (post_id, student_id)
            )
        """))
        print("Table choyxona_post_reposts ensures.")
        
        # 4. Add reply_to_comment_id to choyxona_comments
        print("Checking/Adding reply_to_comment_id to choyxona_comments...")
        try:
            await conn.execute(text("ALTER TABLE choyxona_comments ADD COLUMN reply_to_comment_id INTEGER REFERENCES choyxona_comments(id) ON DELETE SET NULL"))
            print("Added reply_to_comment_id")
        except Exception as e:
            print(f"reply_to_comment_id might already exist: {e}")

        # 4b. Add likes_count to choyxona_comments
        print("Checking/Adding likes_count to choyxona_comments...")
        try:
             await conn.execute(text("ALTER TABLE choyxona_comments ADD COLUMN likes_count INTEGER DEFAULT 0"))
             print("Added likes_count to comments")
        except Exception as e:
             print(f"likes_count (comments) might already exist: {e}")

        # 4c. Create choyxona_comment_likes table
        print("Creating choyxona_comment_likes table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS choyxona_comment_likes (
                id SERIAL PRIMARY KEY,
                comment_id INTEGER NOT NULL REFERENCES choyxona_comments(id) ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                CONSTRAINT _user_comment_like_uc UNIQUE (comment_id, student_id)
            )
        """))
        print("Table choyxona_comment_likes ensured.")

        # 5. Backfill counts
        print("Backfilling counts...")
        await conn.execute(text("""
            UPDATE choyxona_posts p
            SET 
                likes_count = (SELECT count(*) FROM choyxona_post_likes l WHERE l.post_id = p.id),
                comments_count = (SELECT count(*) FROM choyxona_comments c WHERE c.post_id = p.id),
                reposts_count = (SELECT count(*) FROM choyxona_post_reposts r WHERE r.post_id = p.id)
        """))
        await conn.execute(text("""
            UPDATE choyxona_comments c
            SET 
                likes_count = (SELECT count(*) FROM choyxona_comment_likes l WHERE l.comment_id = c.id)
        """))
        print("Counts backfilled.")

if __name__ == "__main__":
    asyncio.run(migrate())

import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database.db_connect import engine
from database.models import Base, ChoyxonaPostView

async def migrate():
    print("🚀 Starting migration for Choyxona views...")
    
    async with engine.begin() as conn:
        # 1. Add views_count column to choyxona_posts
        try:
            print("Adding 'views_count' column to 'choyxona_posts'...")
            await conn.execute(text("ALTER TABLE choyxona_posts ADD COLUMN IF NOT EXISTS views_count INTEGER DEFAULT 0"))
            print("✅ Column 'views_count' added or already exists.")
        except Exception as e:
            print(f"⚠️ Error adding 'views_count' column: {e}")

        # 2. Create choyxona_post_views table
        try:
            print("Creating 'choyxona_post_views' table...")
            # We can use Base.metadata.create_all but we only want this table
            await conn.run_sync(Base.metadata.create_all, tables=[ChoyxonaPostView.__table__])
            print("✅ Table 'choyxona_post_views' created or already exists.")
        except Exception as e:
            print(f"⚠️ Error creating 'choyxona_post_views' table: {e}")

    print("🏁 Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

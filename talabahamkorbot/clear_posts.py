import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal

async def clear_community_data():
    async with AsyncSessionLocal() as db:
        print("Clearing Choyxona Posts and Likes...")
        
        # Order matters for foreign keys
        await db.execute(text("DELETE FROM choyxona_post_likes"))
        await db.execute(text("DELETE FROM choyxona_post_reposts"))
        await db.execute(text("DELETE FROM choyxona_comments"))
        await db.execute(text("DELETE FROM choyxona_posts"))
        
        await db.commit()
        print("Successfully cleared all community data.")

if __name__ == "__main__":
    asyncio.run(clear_community_data())

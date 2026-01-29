
import asyncio
from database.db_connect import engine
from database.models import Base

async def create_table():
    async with engine.begin() as conn:
        print("Creating choyxona_post_likes table...")
        # Create only the specific table if possible, or all (since checkfirst=True)
        await conn.run_sync(Base.metadata.create_all)
        print("Done.")

if __name__ == "__main__":
    asyncio.run(create_table())

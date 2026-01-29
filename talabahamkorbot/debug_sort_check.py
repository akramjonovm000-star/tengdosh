import asyncio
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import async_sessionmaker
from database.db_connect import engine
from database.models import ChoyxonaComment

async def check_sort():
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as db:
        # Get comments for a post (any post with multiple comments)
        # We'll just grab last 10 comments globally to check sort
        query = select(ChoyxonaComment).order_by(ChoyxonaComment.created_at.asc()).limit(5)
        result = await db.execute(query)
        comments = result.scalars().all()
        
        print("--- ASC ORDER TEST ---")
        for c in comments:
            print(f"ID: {c.id}, Content: {c.content}, Time: {c.created_at}")

        query_desc = select(ChoyxonaComment).order_by(ChoyxonaComment.created_at.desc()).limit(5)
        result = await db.execute(query_desc)
        comments_desc = result.scalars().all()
        
        print("\n--- DESC ORDER TEST ---")
        for c in comments_desc:
            print(f"ID: {c.id}, Content: {c.content}, Time: {c.created_at}")

if __name__ == "__main__":
    asyncio.run(check_sort())

import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, ChoyxonaPost

async def main():
    async with AsyncSessionLocal() as session:
        # Search for student 729 posts
        print("--- Choyxona Posts for Student 729 ---")
        stmt = select(ChoyxonaPost).where(ChoyxonaPost.student_id == 729)
        result = await session.execute(stmt)
        posts = result.scalars().all()
        print(f"Post count: {len(posts)}")
        for p in posts:
            print(f"Post ID: {p.id} | Content: {p.content[:50]}... | Created: {p.created_at}")

        # Search for ANY post with "Akramjonov" or "Muhammadali"
        print("\n--- Choyxona Posts with search terms ---")
        stmt = select(ChoyxonaPost).where(ChoyxonaPost.content.ilike("%Muhammadali%") | ChoyxonaPost.content.ilike("%Akramjonov%"))
        result = await session.execute(stmt)
        for p in result.scalars():
             print(f"Post ID: {p.id} | Student ID: {p.student_id} | Content: {p.content[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())

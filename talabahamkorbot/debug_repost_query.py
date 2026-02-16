import asyncio
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaPostRepost, Student

async def debug_reposts():
    async with AsyncSessionLocal() as db:
        print("--- DEBUGGING REPOSTS ---")
        
        # 1. Total Count
        count = await db.scalar(select(func.count()).select_from(ChoyxonaPostRepost))
        print(f"Total Reposts in DB: {count}")
        
        if count == 0:
            print("No reposts found in database.")
            return

        # 2. List last 5 reposts (raw)
        print("\nLast 5 Reposts (Raw):")
        reposts = await db.execute(select(ChoyxonaPostRepost).order_by(desc(ChoyxonaPostRepost.created_at)).limit(5))
        reposts = reposts.scalars().all()
        
        target_id = None
        for r in reposts:
            print(f"ID: {r.id}, User: {r.student_id}, Post: {r.post_id}, Time: {r.created_at}")
            if not target_id: target_id = r.student_id
            
        # 3. Test API Logic for the last reposter
        if target_id:
            print(f"\nTesting API Logic for User ID: {target_id}")
            stmt = select(ChoyxonaPost).join(ChoyxonaPostRepost).options(
                selectinload(ChoyxonaPost.student)
            ).where(ChoyxonaPostRepost.student_id == target_id).order_by(desc(ChoyxonaPostRepost.created_at))
            
            res = await db.execute(stmt)
            posts = res.scalars().all()
            print(f"Query returned {len(posts)} posts.")
            for p in posts:
                print(f"- Post {p.id}: {p.content[:30]}... (Author: {p.student_id})")

if __name__ == "__main__":
    asyncio.run(debug_reposts())

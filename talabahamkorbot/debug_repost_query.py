
import asyncio
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, ChoyxonaPostRepost, Student

async def debug_reposts():
    async with AsyncSessionLocal() as db:
        target_id = 730
        
        # 1. Exact API Query Logic
        stmt = select(ChoyxonaPost).join(ChoyxonaPostRepost).options(
            selectinload(ChoyxonaPost.likes),
            selectinload(ChoyxonaPost.reposts),
            selectinload(ChoyxonaPost.student) # Load author for mapping
        ).where(ChoyxonaPostRepost.student_id == target_id).order_by(desc(ChoyxonaPostRepost.created_at)).limit(20)
        
        print(f"Executing Query for student {target_id}...")
        try:
            result = await db.execute(stmt)
            posts = result.scalars().all()
            print(f"Query returned {len(posts)} posts.")
            
            for p in posts:
                print(f" - Post ID: {p.id}, Content: {p.content[:20]}...")
                
        except Exception as e:
            print(f"Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_reposts())

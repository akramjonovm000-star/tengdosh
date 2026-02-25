import asyncio
import sys
from database.db_connect import AsyncSessionLocal
from sqlalchemy import select, or_, desc
from database.models import ChoyxonaPost, ChoyxonaPostRepost
from sqlalchemy.orm import selectinload

async def test():
    async with AsyncSessionLocal() as db:
        print("Connected")
        stmt = select(ChoyxonaPost).join(ChoyxonaPostRepost).options(
            selectinload(ChoyxonaPost.student) # Only load author
        ).where(
            or_(
                ChoyxonaPostRepost.student_id == 730,
                ChoyxonaPostRepost.staff_id == 730
            )
        ).order_by(desc(ChoyxonaPostRepost.created_at)).offset(0).limit(20)
        
        try:
            result = await db.execute(stmt)
            posts = result.scalars().all()
            print([p.id for p in posts])
        except Exception as e:
            print("DB ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())

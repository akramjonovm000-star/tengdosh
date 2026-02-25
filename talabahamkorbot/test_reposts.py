import asyncio
from database.db_connect import async_session
from sqlalchemy import select, or_
from database.models import ChoyxonaPost, ChoyxonaPostRepost
from sqlalchemy.orm import selectinload

async def test():
    async with async_session() as db:
        stmt = select(ChoyxonaPost).join(ChoyxonaPostRepost).where(
            or_(
                ChoyxonaPostRepost.student_id == 82,
                ChoyxonaPostRepost.staff_id == 82
            )
        )
        print("SQL:", str(stmt))
        result = await db.execute(stmt)
        posts = result.scalars().all()
        print("Posts:", len(posts))

if __name__ == '__main__':
    asyncio.run(test())

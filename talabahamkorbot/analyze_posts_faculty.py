import asyncio
import os
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost, Faculty

async def analyze_posts_faculty():
    async with AsyncSessionLocal() as session:
        # Query to count posts grouped by Faculty.name
        stmt = (
            select(
                Faculty.name,
                func.count(ChoyxonaPost.id).label("post_count")
            )
            .join(Faculty, ChoyxonaPost.target_faculty_id == Faculty.id)
            .group_by(Faculty.name)
            .order_by(func.count(ChoyxonaPost.id).desc())
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        # Get total number of posts with target_faculty_id
        total_stmt = select(func.count(ChoyxonaPost.id)).where(ChoyxonaPost.target_faculty_id.isnot(None))
        total_faculty_posts = (await session.execute(total_stmt)).scalar() or 0

        # Get total number of posts without target_faculty_id (University wide)
        uni_stmt = select(func.count(ChoyxonaPost.id)).where(ChoyxonaPost.target_faculty_id.is_(None))
        uni_posts = (await session.execute(uni_stmt)).scalar() or 0
        
        print("\n📊 CHOYXONA POSTLARI TAHLILI (Fakultetlar bo'yicha):\n")
        print(f"{'FAKULTET (FACULTY)':<60} | {'SONI':<5}")
        print("-" * 70)
        
        for faculty_name, count in rows:
            print(f"{faculty_name:<60} | {count:<5}")
            
        print("-" * 70)
        print(f"{'JAMI FAKULTET POSTLARI':<60} | {total_faculty_posts:<5}")
        print(f"{'UMUMIY (FAKULTETSIZ) POSTLAR':<60} | {uni_posts:<5}")
        print(f"{'JAMI BARCHA POSTLAR':<60} | {total_faculty_posts + uni_posts:<5}\n")

if __name__ == "__main__":
    asyncio.run(analyze_posts_faculty())

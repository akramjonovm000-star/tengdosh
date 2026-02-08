import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff, ChoyxonaPost
from sqlalchemy import select
from api.community import get_posts, get_filters_meta
from unittest.mock import MagicMock

async def run_verification():
    async with AsyncSessionLocal() as db:
        # 1. Find a Dean (PR va menejment - faculty_id=34)
        res = await db.execute(select(Staff).where(Staff.faculty_id == 34).limit(1))
        dean = res.scalar_one_or_none()
        if not dean:
            print("No dean found for faculty 34")
            return
            
        print(f"Testing Choyxona for Dean: {dean.full_name} (Faculty ID: {dean.faculty_id})")
        
        # 2. Test Filters Meta
        meta = await get_filters_meta(student=dean, db=db)
        print("\nFilters Meta (should only show faculty 34):")
        print(meta)
        
        # 3. Test Get Posts (Faculty Category)
        # Pass skip and limit explicitly to avoid Query type error
        posts = await get_posts(category='faculty', skip=0, limit=20, student=dean, db=db)
        print(f"\nFetched {len(posts)} faculty posts for Dean.")
        
        all_correct = True
        for p in posts:
            if p.target_faculty_id != 34:
                print(f"❌ Error: Post {p.id} has target_faculty_id {p.target_faculty_id}, expected 34")
                all_correct = False
        
        if all_correct and len(meta.get("faculties", [])) == 1 and meta["faculties"][0]["id"] == 34:
             print("\n✅ Verification Success: Choyxona faculty restriction applied.")
        else:
             print("\n❌ Verification Failed: Choyxona faculty restriction NOT applied correctly.")

if __name__ == "__main__":
    asyncio.run(run_verification())

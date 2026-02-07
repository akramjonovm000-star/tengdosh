
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import ChoyxonaPost
from sqlalchemy import select

async def check_posts():
    async with AsyncSessionLocal() as db:
        # Check all posts
        result = await db.execute(select(ChoyxonaPost))
        posts = result.scalars().all()
        print(f"Total Posts: {len(posts)}")
        for p in posts:
            print(f"Post {p.id}: Uni={p.target_university_id}, Fac={p.target_faculty_id}, Spec={p.target_specialty_name}, Cat={p.category_type}")

if __name__ == "__main__":
    asyncio.run(check_posts())

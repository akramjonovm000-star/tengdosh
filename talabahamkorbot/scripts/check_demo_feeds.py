import asyncio
import sys
import os

# Add talabahamkorbot directory to path
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../talabahamkorbot/scripts
parent_dir = os.path.dirname(current_dir) # .../talabahamkorbot
sys.path.append(parent_dir)

from database.db_connect import AsyncSessionLocal
from database.models import Announcement, Banner
from sqlalchemy import select

async def check_feeds():
    print(f"Checking database using {AsyncSessionLocal}")
    async with AsyncSessionLocal() as db:
        # Check Announcements
        print("Querying announcements...")
        stmt_ann = select(Announcement).where(Announcement.is_active == True)
        res_ann = await db.execute(stmt_ann)
        announcements = res_ann.scalars().all()
        
        print(f"--- Announcements ({len(announcements)}) ---")
        for a in announcements:
            print(f"ID: {a.id} | Title: {a.title} | Priority: {a.priority} | Exp: {a.expires_at} | UniID: {a.university_id}")

        # Check Banners
        print("Querying banners...")
        stmt_ban = select(Banner).where(Banner.is_active == True)
        res_ban = await db.execute(stmt_ban)
        banners = res_ban.scalars().all()
        
        print(f"\n--- Banners ({len(banners)}) ---")
        for b in banners:
            print(f"ID: {b.id} | Link: {b.link}")

if __name__ == "__main__":
    asyncio.run(check_feeds())

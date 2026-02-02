import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def fix_urls():
    async with AsyncSessionLocal() as db:
        # 1. Fetch images that contain internal IPs or wrong hostnames
        res = await db.execute(select(Student).where(Student.image_url.like("%38.242.223.171%") | Student.image_url.like("%localhost%")))
        students = res.scalars().all()
        
        print(f"Found {len(students)} students with wrong URLs.")
        
        count = 0
        for s in students:
            if s.image_url:
                new_url = s.image_url.replace("38.242.223.171", "tengdosh.uzjoku.uz").replace("localhost", "tengdosh.uzjoku.uz")
                # Force http for now since SSL is problematic externally
                if new_url.startswith("https"):
                    new_url = new_url.replace("https", "http", 1)
                
                s.image_url = new_url
                count += 1
        
        await db.commit()
        print(f"Cleaned up {count} URLs.")

if __name__ == "__main__":
    asyncio.run(fix_urls())

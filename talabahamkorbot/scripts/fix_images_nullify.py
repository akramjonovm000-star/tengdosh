import asyncio
import sys
import os
from sqlalchemy import select, update

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student

async def main():
    logger_msg = ""
    async with AsyncSessionLocal() as session:
        # Find students with HEMIS image URLs
        # We target URLs starting with https://hemis.jmcu.uz or https://hemis.bfa.uz
        stmt = select(Student).where(
            (Student.image_url.ilike("https://hemis.jmcu.uz%")) | 
            (Student.image_url.ilike("https://hemis.bfa.uz%"))
        )
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        count = len(students)
        print(f"Found {count} students with HEMIS images.")
        
        if count > 0:
            print("Nullifying image_url for these students...")
            # Bulk update for efficiency
            stmt_update = update(Student).where(
                (Student.image_url.ilike("https://hemis.jmcu.uz%")) | 
                (Student.image_url.ilike("https://hemis.bfa.uz%"))
            ).values(image_url=None)
            
            await session.execute(stmt_update)
            await session.commit()
            print("Successfully updated student records.")
        else:
            print("No HEMIS images found to clean up.")

if __name__ == "__main__":
    asyncio.run(main())

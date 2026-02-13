import asyncio
import sys
import os
import logging
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    if not HEMIS_ADMIN_TOKEN:
        logger.error("HEMIS_ADMIN_TOKEN is missing!")
        return

    async with AsyncSessionLocal() as session:
        # 1. Identify groups with missing images
        logger.info("Identifying groups with missing images...")
        stmt = select(distinct(Student.group_number)).where(Student.image_url.is_(None))
        result = await session.execute(stmt)
        groups = result.scalars().all()
        
        # Filter out None groups
        groups = [g for g in groups if g]
        
        logger.info(f"Found {len(groups)} groups with students missing images.")
        
        for group_name in groups:
            await sync_group_images(session, group_name)

        await session.commit()
    
    logger.info("Image restoration complete!")

async def sync_group_images(session, group_name):
    logger.info(f"Fetching students for group: {group_name}")
    
    try:
        students, count = await HemisService.get_students_for_groups([group_name], HEMIS_ADMIN_TOKEN)
    except Exception as e:
        logger.error(f"Error fetching group {group_name}: {e}")
        return

    if not students:
        logger.warning(f"No students found for group {group_name} in HEMIS.")
        return

    logger.info(f"Processing {len(students)} students for {group_name}...")
    
    for s_data in students:
        hemis_id = str(s_data.get("id"))
        image_url = s_data.get("image")
        
        if not image_url:
            continue
            
        # Find student in DB
        stmt = select(Student).where(Student.hemis_id == hemis_id)
        result = await session.execute(stmt)
        students_db = result.scalars().all()
        
        for student in students_db:
        # student = result.scalar_one_or_none()
        
        # if student:
            # SAFETY CHECK: Only update if currently NULL or empty
            # We assume custom images (with static/uploads) are already set and strictly protected
            if not student.image_url:
                student.image_url = image_url
                # logger.info(f"Updated image for {student.full_name}")

if __name__ == "__main__":
    asyncio.run(main())

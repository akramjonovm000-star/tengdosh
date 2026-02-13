import asyncio
import re
import sys
import os
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def count_initials(name):
    if not name: return 99
    return len(re.findall(r'\b[A-Z]\.', name))

async def fix_names():
    if not HEMIS_ADMIN_TOKEN:
        logger.error("HEMIS_ADMIN_TOKEN is missing!")
        return

    async with AsyncSessionLocal() as session:
        # 1. Identify groups that need fixing
        res = await session.execute(select(Student.full_name, Student.group_number))
        rows = res.all()
        
        groups_to_sync = set()
        for full_name, group_number in rows:
            if re.search(r'\b[A-Z]\.', full_name) and group_number:
                groups_to_sync.add(group_number)
        
        groups_to_sync = list(groups_to_sync)
        logger.info(f"Syncing {len(groups_to_sync)} groups...")
        
        # 2. Sync group by group
        processed_groups = 0
        total_updated = 0
        
        for group_name in groups_to_sync:
            logger.info(f"[{processed_groups+1}/{len(groups_to_sync)}] Syncing group: {group_name}...")
            
            try:
                students_data, count = await HemisService.get_students_for_groups([group_name], HEMIS_ADMIN_TOKEN)
                if not students_data:
                    logger.warning(f"No data for group {group_name}")
                    processed_groups += 1
                    continue
                
                # Map by hemis_id for quick lookup
                data_map = {str(s.get("id")): s for s in students_data}
                
                # Fetch current students in DB for this group
                stmt = select(Student).where(Student.group_number == group_name)
                db_res = await session.execute(stmt)
                db_students = db_res.scalars().all()
                
                for student in db_students:
                    s_data = data_map.get(str(student.hemis_id))
                    if not s_data: continue
                    
                    # Extract names
                    f_name = (s_data.get('first_name') or "").strip().title()
                    l_name = (s_data.get('second_name') or "").strip().title()
                    p_name = (s_data.get('third_name') or "").strip().title()
                    
                    constructed = f"{l_name} {f_name} {p_name}".strip()
                    hemis_short = (s_data.get("short_name") or "").strip().title()
                    
                    # Choose best full name
                    if count_initials(constructed) <= count_initials(hemis_short) and len(constructed) > 5:
                        best_full = constructed
                    else:
                        best_full = hemis_short or student.full_name
                    
                    # Update if better
                    if count_initials(best_full) < count_initials(student.full_name) or (len(best_full) > len(student.full_name) and count_initials(best_full) <= count_initials(student.full_name)):
                        logger.info(f"  Updating: {student.full_name} -> {best_full}")
                        student.full_name = best_full
                        student.short_name = f_name or best_full.split()[0]
                        total_updated += 1
                
                await session.commit()
                processed_groups += 1
                
            except Exception as e:
                logger.error(f"Error syncing group {group_name}: {e}")
                await session.rollback()
        
        logger.info(f"Done! Updated {total_updated} students across {processed_groups} groups.")

if __name__ == "__main__":
    asyncio.run(fix_names())

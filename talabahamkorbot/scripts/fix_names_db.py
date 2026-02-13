import asyncio
import logging
import sys
import os

# Adjust path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff, User
from utils.text_utils import format_uzbek_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_names():
    async with AsyncSessionLocal() as db:
        logger.info("Starting Name Correction Migration...")
        
        # 1. Fix Students
        logger.info("Scanning Students...")
        result = await db.execute(select(Student))
        students = result.scalars().all()
        s_count = 0
        
        for s in students:
            if not s.full_name: continue
            
            original = s.full_name
            corrected = format_uzbek_name(original)
            
            if original != corrected:
                s.full_name = corrected
                s_count += 1
                logger.info(f"Student: {original} -> {corrected}")
                
        # 2. Fix Staff
        logger.info("Scanning Staff...")
        result = await db.execute(select(Staff))
        staff_list = result.scalars().all()
        st_count = 0
        
        for st in staff_list:
            if not st.full_name: continue
            
            original = st.full_name
            corrected = format_uzbek_name(original)
            
            if original != corrected:
                st.full_name = corrected
                st_count += 1
                logger.info(f"Staff: {original} -> {corrected}")

        # 3. Fix Users (Unified Auth Table)
        logger.info("Scanning Users...")
        result = await db.execute(select(User))
        users = result.scalars().all()
        u_count = 0
        
        for u in users:
            if not u.full_name: continue
            
            original = u.full_name
            corrected = format_uzbek_name(original)
            
            if original != corrected:
                u.full_name = corrected
                u_count += 1
                logger.info(f"User: {original} -> {corrected}")
        
        if s_count > 0 or st_count > 0 or u_count > 0:
            logger.info(f"Committing changes: Students={s_count}, Staff={st_count}, Users={u_count}")
            await db.commit()
        else:
            logger.info("No changes needed.")

if __name__ == "__main__":
    asyncio.run(fix_names())

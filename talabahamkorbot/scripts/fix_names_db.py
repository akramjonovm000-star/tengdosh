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
            changed = False
            # Fix Full Name
            if s.full_name:
                new_full = format_uzbek_name(s.full_name)
                if new_full != s.full_name:
                    print(f"Student Full: {s.full_name} -> {new_full}")
                    s.full_name = new_full
                    changed = True
            
            # Fix Short Name
            if s.short_name:
                new_short = format_uzbek_name(s.short_name)
                if new_short != s.short_name:
                    print(f"Student Short: {s.short_name} -> {new_short}")
                    s.short_name = new_short
                    changed = True
            
            if changed: s_count += 1
                
        # 2. Fix Staff
        logger.info("Scanning Staff...")
        result = await db.execute(select(Staff))
        staff_list = result.scalars().all()
        st_count = 0
        
        for st in staff_list:
            changed = False
            if st.full_name:
                new_full = format_uzbek_name(st.full_name)
                if new_full != st.full_name:
                    print(f"Staff Full: {st.full_name} -> {new_full}")
                    st.full_name = new_full
                    changed = True
            if changed: st_count += 1

        # 3. Fix Users (Unified Auth Table)
        logger.info("Scanning Users...")
        result = await db.execute(select(User))
        users = result.scalars().all()
        u_count = 0
        
        for u in users:
            changed = False
            # Fix Full Name
            if u.full_name:
                new_full = format_uzbek_name(u.full_name)
                if new_full != u.full_name:
                    print(f"User Full: {u.full_name} -> {new_full}")
                    u.full_name = new_full
                    changed = True
            
            # Fix Short Name
            if u.short_name:
                new_short = format_uzbek_name(u.short_name)
                if new_short != u.short_name:
                    print(f"User Short: {u.short_name} -> {new_short}")
                    u.short_name = new_short
                    changed = True
            
            if changed: u_count += 1
        
        if s_count > 0 or st_count > 0 or u_count > 0:
            logger.info(f"Committing changes: Students={s_count}, Staff={st_count}, Users={u_count}")
            await db.commit()
        else:
            logger.info("No changes needed. Database is clean.")

if __name__ == "__main__":
    asyncio.run(fix_names())

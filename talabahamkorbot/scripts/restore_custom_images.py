import asyncio
import sys
import os
import re
from sqlalchemy import select, update

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student, Staff
from config import DOMAIN

# Regex to parse filenames: student_123_1770818484.jpg
FILE_PATTERN = re.compile(r"^(student|staff)_(\d+)_(\d+)\.(jpg|png|jpeg)$")
# Legacy pattern: 123_1770818484.jpg (Assumed to be student)
LEGACY_PATTERN = re.compile(r"^(\d+)_(\d+)\.(jpg|png|jpeg)$")

UPLOAD_DIR = "static/uploads"

async def main():
    if not DOMAIN:
        print("ERROR: DOMAIN not found in config.")
        return

    print(f"Scanning {UPLOAD_DIR}...")
    
    # Store latest file for each entity: key=(prefix, id), value=(timestamp, filename)
    latest_files = {}
    
    try:
        files = os.listdir(UPLOAD_DIR)
    except FileNotFoundError:
        print(f"Directory {UPLOAD_DIR} not found.")
        return

    for f in files:
        # Check Standard Pattern
        match = FILE_PATTERN.match(f)
        if match:
            prefix, entity_id, timestamp_str, ext = match.groups()
            entity_id = int(entity_id)
            timestamp = int(timestamp_str)
            key = (prefix, entity_id)
            
            if key not in latest_files or timestamp > latest_files[key][0]:
                latest_files[key] = (timestamp, f)
            continue
            
        # Check Legacy Pattern
        legacy_match = LEGACY_PATTERN.match(f)
        if legacy_match:
            entity_id, timestamp_str, ext = legacy_match.groups()
            entity_id = int(entity_id)
            timestamp = int(timestamp_str)
            
            # Assume legacy files are STUDENTS
            key = ("student", entity_id)
            
            if key not in latest_files or timestamp > latest_files[key][0]:
                latest_files[key] = (timestamp, f)

    
    print(f"Found {len(latest_files)} unique entities with custom images.")
    
    async with AsyncSessionLocal() as session:
        updates_count = 0
        
        for (prefix, entity_id), (ts, filename) in latest_files.items():
            full_url = f"https://{DOMAIN}/static/uploads/{filename}"
            
            if prefix == "student":
                stmt = select(Student).where(Student.id == entity_id)
                result = await session.execute(stmt)
                student = result.scalar_one_or_none()
                
                if student:
                    # Update only if it's different (or currently None)
                    if student.image_url != full_url:
                        student.image_url = full_url
                        updates_count += 1
                        # print(f"Restoring Student {entity_id}: {full_url}")
            
            elif prefix == "staff":
                stmt = select(Staff).where(Staff.id == entity_id)
                result = await session.execute(stmt)
                staff = result.scalar_one_or_none()
                
                if staff:
                    if staff.image_url != full_url:
                        staff.image_url = full_url
                        updates_count += 1
                        # print(f"Restoring Staff {entity_id}: {full_url}")
        
        await session.commit()
        print(f"Successfully restored {updates_count} images.")

if __name__ == "__main__":
    asyncio.run(main())

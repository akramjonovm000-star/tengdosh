import asyncio
import sys
import os
from sqlalchemy import select

# Add talabahamkorbot directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database.db_connect import AsyncSessionLocal
from database.models import UserActivityImage, UserCertificate, UserDocument

async def find_file_id():
    async with AsyncSessionLocal() as db:
        # Check Activity Images
        stmt = select(UserActivityImage).limit(1)
        res = await db.execute(stmt)
        img = res.scalar_one_or_none()
        if img:
            print(f"FOUND: {img.file_id}")
            return

        # Check Certificates
        stmt = select(UserCertificate).limit(1)
        res = await db.execute(stmt)
        cert = res.scalar_one_or_none()
        if cert:
            print(f"FOUND: {cert.file_id}")
            return
            
        print("NOT_FOUND")

if __name__ == "__main__":
    asyncio.run(find_file_id())

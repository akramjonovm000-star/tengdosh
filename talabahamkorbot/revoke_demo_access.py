
import asyncio
import sys
import os

# Set up path
sys.path.append("/home/user/talabahamkor/talabahamkorbot")

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def revoke_role():
    async with AsyncSessionLocal() as db:
        # Find Student 730
        result = await db.execute(select(Student).where(Student.id == 730))
        student = result.scalar_one_or_none()
        
        if student:
            print(f"Found Student: {student.full_name} ({student.id})")
            print(f"Current Role (HEMIS): {student.hemis_role}")
            
            # Reset Role
            student.hemis_role = 'student'
            student.custom_badge = None
            student.is_premium = False
            student.premium_expiry = None
            
            await db.commit()
            print(f"Success! Role reset to 'student' for {student.full_name}.")
        else:
            print("Student 730 not found.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(revoke_role())

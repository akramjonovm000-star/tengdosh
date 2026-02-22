import asyncio
import json
from sqlalchemy import select, func, or_
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def investigate_students():
    async with AsyncSessionLocal() as db:
        # Search for these two students
        names = ["Murtozayeva Sevinchgul", "Nasriddinova Navbahor"]
        
        for name in names:
            stmt = select(Student).where(
                Student.university_id == 1,
                Student.full_name.ilike(f"%{name}%")
            )
            result = await db.execute(stmt)
            students = result.scalars().all()
            
            for s in students:
                print(f"--- {s.full_name} ---")
                print(f"ID: {s.id}")
                print(f"Group: {s.group_number}")
                print(f"last_active_at: {s.last_active_at}")
                print(f"fcm_token: {s.fcm_token}")
                print(f"username: {s.username}")
                print(f"image_url: {s.image_url}")
                print(f"hemis_token: {s.hemis_token}")
                print(f"hemis_password: {s.hemis_password}")
                print(f"is_premium: {s.is_premium}")
                print(f"created_at: {s.created_at}")

        # Let's see how many total students have an image_url but last_active_at is null
        count_img_no_active = await db.scalar(
            select(func.count(Student.id)).where(
                Student.image_url != None,
                Student.last_active_at == None
            )
        )
        print(f"\nStudents with image_url but NO last_active_at: {count_img_no_active}")
        
        # How about username != None
        count_user_no_active = await db.scalar(
            select(func.count(Student.id)).where(
                Student.username != None,
                Student.last_active_at == None
            )
        )
        print(f"Students with username but NO last_active_at: {count_user_no_active}")
        
        # All users with image_url
        count_img = await db.scalar(
            select(func.count(Student.id)).where(
                Student.image_url != None
            )
        )
        print(f"Total students with image_url: {count_img}")

if __name__ == '__main__':
    asyncio.run(investigate_students())

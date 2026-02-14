import asyncio
import os
import sys
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import User, Student

async def main():
    print("Searching for the 1500th user...")
    async with AsyncSessionLocal() as session:
        # Get 1500th user (Offset 1499)
        query = (
            select(User, Student.faculty_name.label("student_faculty"))
            .outerjoin(Student, User.hemis_login == Student.hemis_login)
            .order_by(User.created_at)
            .offset(1499)
            .limit(1)
        )
        
        result = await session.execute(query)
        row = result.first()
        
        if row:
            user, student_faculty = row
            faculty = user.faculty_name or student_faculty or "Noma'lum"
            
            print(f"\n🎉 1500-FOYDALANUVCHI (Batafsil):")
            print(f"👤 Ism-familiya: {user.full_name}")
            print(f"🆔 HEMIS Login: {user.hemis_login}")
            print(f"🏢 Fakultet: {faculty}")
            print(f"📚 Yo'nalish: {user.specialty_name}")
            print(f"📅 Ro'yxatdan o'tgan: {user.created_at}")
        else:
            print("❌ 1500-foydalanuvchi topilmadi.")

if __name__ == "__main__":
    asyncio.run(main())

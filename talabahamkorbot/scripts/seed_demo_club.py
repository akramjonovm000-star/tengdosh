import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from database.db_connect import AsyncSessionLocal
from database.models import Club, Student

async def main():
    async with AsyncSessionLocal() as session:
        # Run Alter Table to ensure columns exist
        print("Ensuring columns exist...")
        try:
            await session.execute(text("ALTER TABLE clubs ADD COLUMN IF NOT EXISTS telegram_channel_id VARCHAR(64)"))
            await session.execute(text("ALTER TABLE club_memberships ADD COLUMN IF NOT EXISTS telegram_id VARCHAR(64)"))
            await session.execute(text("ALTER TABLE club_memberships ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'"))
            await session.commit()
        except Exception as e:
            print(f"Alter table ignored: {e}")
            await session.rollback()
            
        # 1. Find the student by HEMIS ID
        target_hemis_id = "395251101397"
        student = await session.scalar(
            select(Student).where(Student.hemis_login == target_hemis_id)
        )
        
        if not student:
            print(f"Warning: Student with HEMIS login {target_hemis_id} not found. Could not seed.")
            return
            
        print(f"Found Student: {student.full_name} (ID: {student.id})")
        
        # 2. Check if a demo club already exists, or create a new one
        demo_club_name = "Jurnalistika Ijodkorlari"
        club = await session.scalar(
            select(Club).where(Club.name == demo_club_name)
        )
        
        if club:
            print("Updating existing Club...")
            club.leader_student_id = student.id
            club.telegram_channel_id = "@ichkiovoz"
            club.channel_link = "https://t.me/ichkiovoz"
        else:
            print("Creating new Club...")
            club = Club(
                name=demo_club_name,
                description="Jurnalistika va ommaviy kommunikatsiyalar universiteti ijodkor yoshlari uchun rasmiy klub.",
                icon="campaign",
                color="#2196F3",
                telegram_channel_id="@ichkiovoz",
                channel_link="https://t.me/ichkiovoz",
                leader_student_id=student.id
            )
            session.add(club)
            
        await session.commit()
        print(f"Successfully assigned {student.full_name} as leader of '{demo_club_name}' with channel @ichkiovoz")

if __name__ == "__main__":
    asyncio.run(main())

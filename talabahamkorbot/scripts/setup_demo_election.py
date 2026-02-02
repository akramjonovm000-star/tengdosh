import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'talabahamkorbot'))

from sqlalchemy import select
from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Student, University, Election, ElectionCandidate
from datetime import datetime, timedelta

async def setup_demo_election():
    async with AsyncSessionLocal() as session:
        # 1. Get a university
        univ = await session.scalar(select(University).limit(1))
        if not univ:
            print("No university found in DB")
            return

        print(f"Target University: {univ.name} (id: {univ.id})")

        # 2. Deactivate existing active elections for this university
        existing_elections = await session.scalars(
            select(Election).where(Election.university_id == univ.id, Election.status == "active")
        )
        for e in existing_elections:
            e.status = "finished"
        
        # 3. Create new demo election
        election = Election(
            university_id=univ.id,
            title="Sardorlar demo saylovi",
            description="Ushbu saylov mobil ilova funksiyasini tekshirish uchun yaratilgan demo saylovdir.",
            status="active",
            deadline=datetime.utcnow() + timedelta(days=7),
            is_active=True
        )
        session.add(election)
        await session.flush() # Get election ID
        
        # 4. Get some students to be candidates
        students = await session.scalars(
            select(Student).where(Student.university_id == univ.id).limit(3)
        )
        student_list = list(students)
        
        if not student_list:
            print("No students found to create candidates")
            return

        # 5. Create candidates
        names = ["Abdumajidov Akramjon", "Sardor Salimov", "Dilshod To'rayev"]
        for i, student in enumerate(student_list):
            candidate = ElectionCandidate(
                election_id=election.id,
                student_id=student.id,
                faculty_id=student.faculty_id or 1,
                campaign_text=f"Men {student.full_name or names[i % len(names)]}, talabalarning ovozini eshittirishga va'da beraman! Biz birgalikda universitetimizni yaxshiroq qilamiz.",
                order=i + 1
            )
            session.add(candidate)
            print(f"Created candidate: {student.full_name or names[i % len(names)]}")

        await session.commit()
        print(f"Demo election '{election.title}' (ID: {election.id}) is now ACTIVE.")

if __name__ == "__main__":
    asyncio.run(setup_demo_election())

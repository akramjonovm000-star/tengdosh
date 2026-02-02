import asyncio
import logging
from sqlalchemy import select, and_
from database.db_connect import AsyncSessionLocal
from database.models import Student, Election, ElectionCandidate, University, Faculty

async def create_demo_election():
    async with AsyncSessionLocal() as session:
        # 1. Get a student who is fully registered (has uni and faculty)
        stmt = select(Student).where(
            and_(Student.university_id.is_not(None), Student.faculty_id.is_not(None))
        ).limit(1)
        student = await session.scalar(stmt)
        
        if not student:
            print("No fully registered students found in DB.")
            return

        uni_id = student.university_id
        fac_id = student.faculty_id
        
        print(f"Creating election for Uni: {student.university_name}, Faculty: {student.faculty_name}")

        # 2. Create an election
        election = Election(
            university_id=uni_id,
            title="Sardorlar Saylovi - 2026",
            description="Fakultetimizning eng faol va tashabbuskor talabasini aniqlash vaqti keldi! O'z nomzodingizga ovoz bering.",
            is_active=True
        )
        session.add(election)
        await session.flush()
        
        # 3. Get up to 4 students from the same faculty to be candidates
        cand_stmt = select(Student).where(Student.faculty_id == fac_id).limit(4)
        potential_candidates = (await session.scalars(cand_stmt)).all()
        
        campaigns = [
            "1. Talabalar uchun bepul IT kurslarini yo'lga qo'yish.\n2. Kutubxonadagi kitoblar bazasini yangilash.\n3. Har oyda bir marta 'Fakultet kuni' festivalini o'tkazish.",
            "1. Talabalar turar joyidagi sharoitlarni yaxshilashda yordam berish.\n2. Sport musobaqalari sonini ko'paytirish.\n3. 'Talaba almashinuvi' dasturlarini faollashtirish.",
            "1. Universitetda startap loyihalarni qo'llab-quvvatlash markazini ochish.\n2. Xorijiy mutaxassislar bilan master-klasslar tashkil etish.\n3. Talabalar uchun chegirmali o'quv markazlari bilan hamkorlik qilish.",
            "1. Fakultetimizda zamonaviy coworking markazi ochish.\n2. Karyera markazini rivojlantirish va talabalarni ish bilan ta'minlashda yordam berish.\n3. Talabalar murojaatlari uchun bot va ishonch telefoni yaratish."
        ]
        
        for i, cand_student in enumerate(potential_candidates):
            candidate = ElectionCandidate(
                election_id=election.id,
                student_id=cand_student.id,
                faculty_id=fac_id,
                campaign_text=campaigns[i % len(campaigns)],
                order=i+1
            )
            session.add(candidate)
            print(f"Added candidate: {cand_student.full_name}")
            
        await session.commit()
        print(f"\n✅ Demo election created successfully!")
        print(f"📌 Uni ID: {uni_id}, Faculty ID: {fac_id}")

if __name__ == "__main__":
    asyncio.run(create_demo_election())

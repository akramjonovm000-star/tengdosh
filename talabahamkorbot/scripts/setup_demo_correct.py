import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import get_session, AsyncSessionLocal
from database.models import Staff, TutorGroup, Student, StudentFeedback, University, Faculty

async def setup_demo_data():
    async with AsyncSessionLocal() as session:
        print("🚀 Setting up Demo Data for Correct Tutor Login...")
        
        # 1. Match api/auth.py credentials for login="tyutor"
        # In api/auth.py: jshshir="12345678901234", hemis_id=999999
        target_jshshir = "12345678901234"
        target_hemis_id = 999999
        
        # Ensure Uni/Fac exist
        uni = await session.execute(select(University).limit(1))
        uni = uni.scalar()
        if not uni:
            uni = University(name="Demo University", uni_code="DEMO")
            session.add(uni)
            await session.flush()
        
        fac = await session.execute(select(Faculty).limit(1))
        fac = fac.scalar()
        if not fac:
            fac = Faculty(name="Demo Faculty", faculty_code="DEMO_FAC", university_id=uni.id)
            session.add(fac)
            await session.flush()

        # 2. Get or Create the CORRECT Tutor
        tutor_stmt = select(Staff).where(Staff.jshshir == target_jshshir)
        result = await session.execute(tutor_stmt)
        tutor = result.scalar()

        if not tutor:
            tutor = Staff(
                full_name="Demo Tyutor",
                jshshir=target_jshshir,
                hemis_id=target_hemis_id,
                role="tyutor", # api/auth.py uses 'tyutor' text
                phone="+998901234567",
                university_id=uni.id, 
                faculty_id=fac.id,
                is_active=True
            )
            session.add(tutor)
            await session.commit()
            print(f"✅ Created Correct Tutor: {tutor.full_name} (Login: tyutor)")
        else:
            print(f"ℹ️ Found Correct Tutor: {tutor.full_name}")

        # 3. Assign Groups to THIS Tutor
        demo_groups = ["DEMO-301", "DEMO-302"]
        
        for gr_num in demo_groups:
            # Check assignment
            tg_stmt = select(TutorGroup).where(
                TutorGroup.tutor_id == tutor.id,
                TutorGroup.group_number == gr_num
            )
            tg = (await session.execute(tg_stmt)).scalar()
            
            if not tg:
                tg = TutorGroup(
                    tutor_id=tutor.id,
                    group_number=gr_num,
                    university_id=uni.id,
                    faculty_id=fac.id
                )
                session.add(tg)
                print(f"✅ Assigned Group {gr_num} to 'tyutor'")
            else:
                print(f"ℹ️ Group {gr_num} already assigned to 'tyutor'")

        await session.commit()

        # 4. Ensure Students Exist (Reuse previous logic)
        students_data = [
            {"name": "Talaba Bir", "group": "DEMO-301", "appeals": ["Stipendiyam tushmadi, yordam bering.", "Kontrakt to'lovini bo'lib to'lasam bo'ladimi?"]},
            {"name": "Talaba Uch", "group": "DEMO-302", "appeals": ["Yotoqxona bo'yicha savolim bor edi."]},
        ]

        for s_data in students_data:
            stmt = select(Student).where(Student.hemis_login == f"login_{s_data['name'].replace(' ', '_')}")
            student = (await session.execute(stmt)).scalar()
            
            if not student:
                student = Student(
                    full_name=s_data['name'],
                    hemis_login=f"login_{s_data['name'].replace(' ', '_')}",
                    group_number=s_data['group'],
                    university_id=uni.id,
                    faculty_id=fac.id,
                    is_active=True
                )
                session.add(student)
                await session.flush()

            # Create Appeals
            for appeal_text in s_data['appeals']:
                fb_stmt = select(StudentFeedback).where(
                    StudentFeedback.student_id == student.id,
                    StudentFeedback.text == appeal_text
                )
                fb = (await session.execute(fb_stmt)).scalar()
                
                if not fb:
                    fb = StudentFeedback(
                        student_id=student.id,
                        text=appeal_text,
                        status="pending"
                    )
                    session.add(fb)
                    print(f"   -> Added Appeal for {s_data['name']}")

        await session.commit()
        print("\n🎉 Correction Complete!")
        print(f"Login: tyutor")
        print(f"Parol: 123")
        print(f"Groups: {demo_groups}")

if __name__ == "__main__":
    asyncio.run(setup_demo_data())

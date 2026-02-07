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
        print("🚀 Setting up Demo Data for Tutor Appeals...")

        # 1. Ensure University and Faculty exist
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

        # 2. Create/Get Demo Tutor
        # User said "tyutor 123", let's assume hemis_id=123 or similar
        tutor_stmt = select(Staff).where(Staff.role == 'tyutor', Staff.jshshir == '123123123')
        result = await session.execute(tutor_stmt)
        tutor = result.scalar()

        if not tutor:
            tutor = Staff(
                full_name="Demo Tyutor 123",
                jshshir="123123123",
                role="tyutor",
                phone="+998901234567",
                university_id=uni.id,
                faculty_id=fac.id,
                is_active=True
            )
            session.add(tutor)
            await session.commit()
            print(f"✅ Created Tutor: {tutor.full_name} (ID: {tutor.id})")
        else:
            print(f"ℹ️ Found Tutor: {tutor.full_name} (ID: {tutor.id})")

        # 3. Create Demo Groups and Assign to Tutor
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
                print(f"✅ Assigned Group {gr_num} to Tutor")
            else:
                print(f"ℹ️ Group {gr_num} already assigned")

        await session.commit()

        # 4. Create Students and Appeals
        students_data = [
            {"name": "Talaba Bir", "group": "DEMO-301", "appeals": ["Stipendiyam tushmadi, yordam bering.", "Kontrakt to'lovini bo'lib to'lasam bo'ladimi?"]},
            {"name": "Talaba Ikki", "group": "DEMO-301", "appeals": []},
            {"name": "Talaba Uch", "group": "DEMO-302", "appeals": ["Yotoqxona bo'yicha savolim bor edi."]},
        ]

        for s_data in students_data:
            # Check student
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
                print(f"✅ Created Student: {student.full_name}")
            else:
                 print(f"ℹ️ Found Student: {student.full_name}")

            # Create Appeals
            for appeal_text in s_data['appeals']:
                # Check duplicate to avoid spamming on re-runs
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
                    print(f"   -> Added Appeal: {appeal_text}")
                else:
                    print(f"   -> Appeal already exists")

        await session.commit()
        print("\n🎉 Demo data setup complete!")
        print(f"Tutor Name: {tutor.full_name}")
        print(f"Tutor JSHSHIR (Login ref): {tutor.jshshir}")

if __name__ == "__main__":
    asyncio.run(setup_demo_data())

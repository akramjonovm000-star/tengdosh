import asyncio
import sys
import os
import shutil

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import get_session, AsyncSessionLocal
from database.models import Staff, TutorGroup, Student, StudentFeedback, University, Faculty

async def setup_demo_data():
    # 0. Setup Dummy Images
    os.makedirs("static/uploads", exist_ok=True)
    dummy_files = ["demo_cert.jpg", "demo_screenshot.jpg"]
    # Create valid dummy image files (empty or text, browser might not render but file exists)
    # Better: copy a real image if available or just create strict bytes if possible. 
    # For now, let's just make valid text files, though NetworkImage might fail rendering.
    # Actually, let's try to download a placeholder or just assume user will upload real ones later.
    # User said "rasmlar ham qatnashsin" (images should participate). I'll try to use a valid header.
    
    # Simple 1x1 GIF bytes
    gif_1x1 = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    
    for f in dummy_files:
        with open(f"static/uploads/{f}", "wb") as file:
            file.write(gif_1x1)
    
    async with AsyncSessionLocal() as session:
        print("🚀 Setting up Enhanced Demo Data...")
        
        target_jshshir = "12345678901234"
        
        # 1. University & Faculty
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

        # 2. Tutor
        tutor = (await session.execute(select(Staff).where(Staff.jshshir == target_jshshir))).scalar()
        if not tutor:
             tutor = Staff(full_name="Demo Tyutor", jshshir=target_jshshir, hemis_id=999999, role="tyutor", is_active=True, university_id=uni.id, faculty_id=fac.id)
             session.add(tutor)
             await session.commit()

        # 3. Groups
        demo_groups = ["DEMO-301", "DEMO-302"]
        for gr in demo_groups:
             tg = (await session.execute(select(TutorGroup).where(TutorGroup.tutor_id==tutor.id, TutorGroup.group_number==gr))).scalar()
             if not tg:
                 session.add(TutorGroup(tutor_id=tutor.id, group_number=gr, university_id=uni.id, faculty_id=fac.id))
        await session.commit()

        # 4. Students & Appeals (Mixed with Images)
        students_config = [
            {
                "name": "Talaba Bir", "group": "DEMO-301", 
                "appeals": [
                    {"text": "Mening stipendiyam kechikyapti, bu bo'yicha ma'lumot bera olasizmi?", "file": None},
                    {"text": "Kontrakt to'lov kvitansiyasini yukladim.", "file": "demo_cert.jpg", "type": "image"}
                ]
            },
            {
                "name": "Talaba Ikki", "group": "DEMO-301", 
                "appeals": []
            },
            {
                "name": "Talaba Uch", "group": "DEMO-302", 
                "appeals": [
                    {"text": "Yotoqxona bo'yicha ariza yozgandim, holati nima bo'ldi?", "file": None},
                    {"text": "Mana bu rasmda yotoqxona sharoiti.", "file": "demo_screenshot.jpg", "type": "image"}
                ]
            },
            {
                "name": "Talaba To'rt", "group": "DEMO-302", 
                "appeals": [
                    {"text": "Fanlardan qarzdorlikni qanday yopsam bo'ladi?", "file": None}
                ]
            }
        ]

        for s_conf in students_config:
            login = f"login_{s_conf['name'].replace(' ', '_')}"
            student = (await session.execute(select(Student).where(Student.hemis_login == login))).scalar()
            
            if not student:
                student = Student(
                    full_name=s_conf['name'],
                    hemis_login=login,
                    group_number=s_conf['group'],
                    university_id=uni.id,
                    faculty_id=fac.id,
                    is_active=True
                )
                session.add(student)
                await session.flush()
            else:
                # Update group to ensure correctness
                student.group_number = s_conf['group']
                session.add(student)

            # Add Appeals
            for app in s_conf['appeals']:
                # Check exist
                fb = (await session.execute(select(StudentFeedback).where(StudentFeedback.student_id==student.id, StudentFeedback.text==app['text']))).scalar()
                if not fb:
                    fb = StudentFeedback(
                        student_id=student.id,
                        text=app['text'],
                        status="pending",
                        file_id=app.get('file'),
                        file_type=app.get('file_type')
                    )
                    session.add(fb)
                    print(f"Added appeal for {s_conf['name']}: {app['text'][:20]}...")

        await session.commit()
        print("\n🎉 Enhanced Demo Data with Images Ready!")

if __name__ == "__main__":
    asyncio.run(setup_demo_data())

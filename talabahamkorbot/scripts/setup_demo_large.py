import asyncio
import sys
import os
import random

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup, Student, StudentFeedback, University, Faculty

# Sample Data
APPEAL_TEMPLATES = [
    ("Mening stipendiyam kechikyapti, yordam bering.", None),
    ("Kontrakt to'lovini amalga oshirdim, kvitansiya ilovada.", "demo_pay.jpg"),
    ("Yotoqxona masalasida kimga murojaat qilsam bo'ladi?", None),
    ("Fanlardan qarzdorlikni yopish uchun nima qilishim kerak?", None),
    ("Mana bu sertifikatni yuklamoqchi edim.", "demo_cert.jpg"),
    ("Dars jadvalida xatolik borga o'xshaydi.", "demo_schedule.jpg"),
    ("Ma'lumotnoma kerak edi, qayerdan olsam bo'ladi?", None),
    ("Men kasal bo'lib qoldim, tibbiy ma'lumotnoma yuboryapman.", "demo_med.jpg"),
]

FIRST_NAMES = ["Anvar", "Nodira", "Jasur", "Malika", "Sardor", "Dildora", "Bobur", "Shahnoza", "Doniyor", "Laylo"]
LAST_NAMES = ["Karimov", "Aliyeva", "Rahimov", "Umarova", "Abdullayev", "Yusupova", "Tursunov", "Saidova", "Rustamov", "Oripova"]

async def setup_large_demo_data():
    # 0. Setup Dummy Images
    os.makedirs("static/uploads", exist_ok=True)
    dummy_images = ["demo_pay.jpg", "demo_cert.jpg", "demo_schedule.jpg", "demo_med.jpg"]
    
    # 1x1 Grey Pixel GIF
    gif_1x1 = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    
    for f in dummy_images:
        path = f"static/uploads/{f}"
        if not os.path.exists(path):
            with open(path, "wb") as file:
                file.write(gif_1x1)

    async with AsyncSessionLocal() as session:
        print("🚀 Setting up LARGE Demo Data (10 Groups, Random Appeals)...")
        
        target_jshshir = "12345678901234"
        
        # 1. Ensure Uni/Fac
        uni = await session.execute(select(University).limit(1))
        uni = uni.scalar()
        if not uni:
            uni = University(name="Demo University", uni_code="DEMO")
            session.add(uni)
            await session.flush()
        
        fac = await session.execute(select(Faculty).limit(1))
        fac = fac.scalar()
        if not fac:
            fac = Faculty(name="IT Fakulteti", faculty_code="IT_FAC", university_id=uni.id)
            session.add(fac)
            await session.flush()

        # 2. Get Tutor
        tutor = (await session.execute(select(Staff).where(Staff.jshshir == target_jshshir))).scalar()
        if not tutor:
             print("❌ Error: Demo Tutor not found. Run setup_demo_correct.py first.")
             return

        # 3. Create 10 Groups
        groups = [f"DEMO-3{i:02d}" for i in range(1, 11)] # DEMO-301 to DEMO-310
        
        for gr_num in groups:
            # Create Group
            tg = (await session.execute(select(TutorGroup).where(TutorGroup.tutor_id==tutor.id, TutorGroup.group_number==gr_num))).scalar()
            if not tg:
                session.add(TutorGroup(tutor_id=tutor.id, group_number=gr_num, university_id=uni.id, faculty_id=fac.id))
                print(f"✅ Created Group {gr_num}")
            
            # Create 2-3 Students per Group
            num_students = random.randint(2, 3)
            for _ in range(num_students):
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                full_name = f"{fname} {lname}"
                login = f"login_{fname.lower()}_{lname.lower()}_{random.randint(100,999)}"
                
                student = (await session.execute(select(Student).where(Student.hemis_login == login))).scalar()
                if not student:
                    student = Student(
                        full_name=full_name,
                        hemis_login=login,
                        group_number=gr_num,
                        university_id=uni.id,
                        faculty_id=fac.id,
                        is_active=True,
                        image_url=None # Can leave empty or set random
                    )
                    session.add(student)
                    await session.flush()
                
                # Create 0-2 Appeals per Student
                num_appeals = random.randint(0, 2)
                for _ in range(num_appeals):
                    template_text, template_img = random.choice(APPEAL_TEMPLATES)
                    
                    # Avoid dups for same student (simple check)
                    exists = (await session.execute(select(StudentFeedback).where(StudentFeedback.student_id==student.id, StudentFeedback.text==template_text))).scalar()
                    if not exists:
                        fb = StudentFeedback(
                            student_id=student.id,
                            text=template_text,
                            status="pending", # All pending for demo impact
                            file_id=template_img,
                            file_type="image" if template_img else None
                        )
                        session.add(fb)
                        print(f"   -> Appeal from {full_name} in {gr_num}: {template_text[:30]}...")

        await session.commit()
        print("\n🎉 LARGE Demo Data Setup Complete!")

if __name__ == "__main__":
    asyncio.run(setup_large_demo_data())


import asyncio
import json
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def analyze_users():
    async with AsyncSessionLocal() as session:
        # 1. Total Students (indicates at least one login)
        total_stmt = select(func.count(Student.id))
        total_count = await session.scalar(total_stmt)
        
        # 2. Group by Faculty
        faculty_stmt = select(
            Student.faculty_name, 
            func.count(Student.id)
        ).group_by(Student.faculty_name).order_by(func.count(Student.id).desc())
        
        faculty_res = await session.execute(faculty_stmt)
        faculty_stats = faculty_res.all()
        
        # 3. Group by Specialty and Group within Faculty
        specialty_stmt = select(
            Student.faculty_name,
            Student.specialty_name,
            Student.group_number,
            func.count(Student.id)
        ).group_by(Student.faculty_name, Student.specialty_name, Student.group_number).order_by(Student.faculty_name, Student.specialty_name, Student.group_number)
        
        specialty_res = await session.execute(specialty_stmt)
        specialty_stats = specialty_res.all()
        
        # Formatting output
        print(f"Barcha kirgan talabalar soni: {total_count}\n")
        print("--- FAKULTETLAR BO'YICHA ---")
        for faculty, count in faculty_stats:
            print(f"{faculty or 'Nomalum'}: {count} ta")
            
        print("\n--- GURUHLAR BO'YICHA ---")
        current_faculty = None
        current_specialty = None
        
        for faculty, specialty, group, count in specialty_stats:
            if faculty != current_faculty:
                print(f"\n======== {faculty or 'Nomalum'} ========")
                current_faculty = faculty
                current_specialty = None # Reset specialty for new faculty
            
            if specialty != current_specialty:
                print(f"\n  >> {specialty or 'Nomalum'}:")
                current_specialty = specialty
                
            print(f"      - {group or 'Nomalum'}: {count} ta")

if __name__ == "__main__":
    asyncio.run(analyze_users())

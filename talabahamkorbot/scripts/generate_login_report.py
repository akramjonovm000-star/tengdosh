import asyncio
import csv
import os
import sys
from datetime import datetime
from sqlalchemy import select, func

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount, TutorGroup, Staff

async def main():
    print("Generating report...")
    async with AsyncSessionLocal() as session:
        # Fetch data
        query = (
            select(
                Student.full_name,
                Student.faculty_name,
                Student.specialty_name,
                Student.group_number,
                Student.phone,
                Student.hemis_id,
                TgAccount.id.label("tg_id"),
                Staff.full_name.label("tutor_name")
            )
            .outerjoin(TgAccount, Student.id == TgAccount.student_id)
            .outerjoin(TutorGroup, Student.group_number == TutorGroup.group_number)
            .outerjoin(Staff, TutorGroup.tutor_id == Staff.id)
            .order_by(Student.faculty_name, Student.group_number, Student.full_name)
        )
        
        result = await session.execute(query)
        students = result.all()
        
        # Prepare CSV
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/talabalar_kirish_hisoboti_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        total = 0
        registered = 0
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Fakultet", "Yo'nalish", "Guruh", "Tyutor", "F.I.SH", "Telefon", "HEMIS ID", "Status"])
            
            for s in students:
                is_reg = "Kirgan" if s.tg_id else "Kirmagan"
                if s.tg_id: registered += 1
                total += 1
                
                writer.writerow([
                    s.faculty_name or "-",
                    s.specialty_name or "-",
                    s.group_number or "-",
                    s.tutor_name or "Biriktirilmagan",
                    s.full_name,
                    s.phone or "-",
                    s.hemis_id or "-",
                    is_reg
                ])
                
        print(f"REPORT_PATH: {os.path.abspath(filename)}")
        percent = (registered / total * 100) if total > 0 else 0
        print(f"STATS: Total={total}, Registered={registered}, Percent={percent:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())

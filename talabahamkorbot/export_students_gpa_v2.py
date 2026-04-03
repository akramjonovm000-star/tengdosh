import asyncio
import pandas as pd
from database.db_connect import AsyncSessionLocal
from database.models import Student, UserActivity
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as db:
        query = select(Student).where(
            Student.specialty_name.ilike("%Axborot xizmati va jamoatchilik%"),
            Student.level_name.ilike("%1-kurs%")
        )
        
        result = await db.execute(query)
        students = result.scalars().all()
        
        data = []
        for s in students:
            # Count approved social activities
            act_query = select(func.count(UserActivity.id)).where(
                UserActivity.student_id == s.id,
                UserActivity.status == 'approved'
            )
            act_count = await db.scalar(act_query) or 0
            
            gpa = s.gpa or 0.0
            gpa_f = float(gpa)
            gpa_weighted = round(gpa_f * 16, 2)
            
            # Use 'payment_form' as requested by the user's need for Grant/Contract
            payment_form = s.payment_form or "Noma'lum"
            
            data.append({
                "F.I.SH.": s.full_name,
                "Guruh": s.group_number,
                "To'lov shakli": payment_form,
                "GPA": gpa,
                "GPA * 16 (Max 80)": gpa_weighted,
                "Ijtimoiy faolliklar (soni)": act_count,
                "Login": s.hemis_login
            })
        
        if not data:
            print("No students found.")
            return

        df = pd.DataFrame(data)
        output_file = "axborot_xizmati_1_kurs_gpa_to'lov_bilan.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Exported {len(data)} students to {output_file}")

asyncio.run(main())

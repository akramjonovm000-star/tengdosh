import asyncio
import os
import sys
from sqlalchemy import select
from collections import defaultdict
from datetime import datetime
from aiogram import Bot
from aiogram.types import FSInputFile

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BOT_TOKEN, OWNER_TELEGRAM_ID
from database.db_connect import AsyncSessionLocal
from database.models import User, Student, TutorGroup, Staff

async def main():
    print("Generating corrected report...")
    async with AsyncSessionLocal() as session:
        # Fetch data with coalescing logic (prioritize Student if User is null)
        # We fetch columns from both and decide in Python for simplicity and debugging
        query = (
            select(
                User.full_name,
                User.faculty_name.label("user_faculty"),
                User.specialty_name.label("user_spec"),
                User.group_number.label("user_group"),
                Student.faculty_name.label("student_faculty"),
                Student.specialty_name.label("student_spec"),
                Student.group_number.label("student_group"),
                Staff.full_name.label("tutor_name")
            )
            .outerjoin(Student, User.hemis_login == Student.hemis_login)
            .outerjoin(TutorGroup, Student.group_number == TutorGroup.group_number)
            .outerjoin(Staff, TutorGroup.tutor_id == Staff.id)
            .where(User.role == 'student')
        )
        
        result = await session.execute(query)
        rows = result.all()
        
        # Organize Data
        detailed_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        stats_data = defaultdict(lambda: defaultdict(int))
        
        total_count = 0
        
        for r in rows:
            # Logic: Use Student data if User data is missing
            fac = r.user_faculty or r.student_faculty or "Noma'lum Fakultet"
            spec = r.user_spec or r.student_spec or "Noma'lum Yo'nalish"
            grp = r.user_group or r.student_group or "Guruhsiz"
            tutor = r.tutor_name or "Biriktirilmagan"
            name = r.full_name
            
            # Populate Detailed Data
            detailed_data[fac][spec][(grp, tutor)].append(name)
            
            # Populate Stats
            stats_data[fac][spec] += 1
            
            total_count += 1
            
        # ==========================================
        # 1. Generate Minimal Stats Report
        # ==========================================
        lines_min = []
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        lines_min.append(f"📊 **PLATFORMA STATISTIKASI (YANGILANGAN)**")
        lines_min.append(f"📅 Vaqt: {now}")
        lines_min.append(f"👥 Jami foydalanuvchilar: **{total_count}** nafar\n")
        lines_min.append("────────────────────────")
        
        for fac, specs in sorted(stats_data.items()):
            fac_total = sum(specs.values())
            lines_min.append(f"🔹 **{fac}** ({fac_total})")
            for spec, count in sorted(specs.items(), key=lambda x: x[1], reverse=True):
                lines_min.append(f"   ▫️ {spec}: **{count}**")
            lines_min.append("")
            
        min_report_text = "\n".join(lines_min)
        
        # Save Minimal Report
        output_dir = "reports"
        os.makedirs(output_dir, exist_ok=True)
        min_filename = f"{output_dir}/platforma_statistika_fixed_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(min_filename, "w", encoding="utf-8") as f:
            f.write(min_report_text)


        # ==========================================
        # 2. Generate Detailed Text Report
        # ==========================================
        lines_det = []
        lines_det.append("="*50)
        lines_det.append(f"PLATFORMA FOYDALANUVCHILARI (Batafsil)")
        lines_det.append(f"Vaqt: {now}")
        lines_det.append(f"Jami: {total_count}")
        lines_det.append("="*50)
        lines_det.append("\n")
        
        for fac, specs in sorted(detailed_data.items()):
            lines_det.append(f"🏢 FAKULTET: {fac.upper()}")
            lines_det.append("-" * 30)
            
            for spec, groups in sorted(specs.items()):
                lines_det.append(f"  📚 Yo'nalish: {spec}")
                
                for (grp, tutor), names in sorted(groups.items()):
                    lines_det.append(f"\n    👥 Guruh: {grp}")
                    lines_det.append(f"    👤 Tyutor: {tutor}")
                    lines_det.append(f"    Talabalar ({len(names)}):")
                    for i, name in enumerate(sorted(names), 1):
                        lines_det.append(f"      {i}. {name}")
                    lines_det.append("") 
                
            lines_det.append("\n" + "*"*40 + "\n")
            
        det_filename = f"{output_dir}/platforma_batafsil_fixed_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(det_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines_det))


        print(f"Reports saved:\n1. {min_filename}\n2. {det_filename}")

        # Send via Telegram
        if BOT_TOKEN and OWNER_TELEGRAM_ID:
            try:
                bot = Bot(token=BOT_TOKEN)
                
                # Send Minimal Stats as Message (if short enough) or File
                if len(min_report_text) < 4000:
                    await bot.send_message(
                        chat_id=OWNER_TELEGRAM_ID,
                        text=min_report_text,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_document(
                        chat_id=OWNER_TELEGRAM_ID,
                        document=FSInputFile(min_filename),
                        caption="📊 Platforma Statistikasi (Qisqacha)"
                    )
                
                # Send Detailed Report as File
                await bot.send_document(
                    chat_id=OWNER_TELEGRAM_ID,
                    document=FSInputFile(det_filename),
                    caption="📄 Platforma Foydalanuvchilari (Batafsil Ro'yxat)"
                )
                
                print("Sent to Telegram.")
                await bot.session.close()
            except Exception as e:
                print(f"Failed to send telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())

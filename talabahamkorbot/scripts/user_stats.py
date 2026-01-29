import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Total Students (Bot + App)
        result = await session.execute(select(func.count(Student.id)))
        total_students = result.scalar()

        # 2. Students with Telegram
        result = await session.execute(select(func.count(TgAccount.id)))
        total_tg_users = result.scalar()

        # 3. Active Sessions (with Tokens)
        result = await session.execute(select(func.count(Student.id)).where(Student.hemis_token.is_not(None)))
        total_active_tokens = result.scalar()

        print(f"\n📊 FOYDALANUVCHILAR STATISTIKASI:\n")
        print(f"👥 Jami Talabalar (Baza): {total_students}")
        print(f"📱 Telegram Ulangan: {total_tg_users}")
        print(f"🔑 Faol Sessiyalar (Tokenli): {total_active_tokens}")
        print("-" * 30)

        # 4. All Registered Students
        print("🆕 Barcha Ro'yxatdan O'tganlar:\n")
        print(f"{'#':<3} | {'Ism Familiya':<30} | {'HEMIS Login':<15} | {'Manba':<8} | {'Vaqt'}")
        print("-" * 80)
        
        stmt = select(Student).options(selectinload(Student.tg_accounts)).order_by(desc(Student.created_at))
        result = await session.execute(stmt)
        students = result.scalars().all()

        for i, s in enumerate(students, 1):
            source = "Telegram" if s.tg_accounts else "App/Web"
            print(f"{i:<3} | {s.full_name[:28]:<30} | {s.hemis_login:<15} | {source:<8} | {s.created_at.strftime('%m-%d %H:%M')}")

if __name__ == "__main__":
    asyncio.run(main())

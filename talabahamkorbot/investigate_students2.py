import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount

async def investigate_students():
    async with AsyncSessionLocal() as db:
        names = ["Murtozayeva Sevinchgul", "Nasriddinova Navbahor"]
        for name in names:
            stmt = select(Student).where(Student.university_id == 1, Student.full_name.ilike(f"%{name}%"))
            result = await db.execute(stmt)
            students = result.scalars().all()
            for s in students:
                print(f"--- {s.full_name} ---")
                
                # Check TG Accounts
                tg_stmt = select(TgAccount).where(TgAccount.student_id == s.id)
                tg_res = await db.execute(tg_stmt)
                tgs = tg_res.scalars().all()
                for tg in tgs:
                    print(f"  TG Account: {tg.telegram_id}, last_active: {tg.last_active}")
                if not tgs:
                    print("  No TG accounts linked.")

if __name__ == '__main__':
    asyncio.run(investigate_students())

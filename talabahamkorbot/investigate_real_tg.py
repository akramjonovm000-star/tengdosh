import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount, UserActivity

async def main():
    async with AsyncSessionLocal() as session:
        tg_id = 387178074 # FOUND FROM LOGS
        print(f"--- Investigating TG ID: {tg_id} ---")
        
        stmt = select(TgAccount).where(TgAccount.telegram_id == tg_id)
        result = await session.execute(stmt)
        tg_acc = result.scalar_one_or_none()
        
        if tg_acc:
            print(f"Linked Student ID: {tg_acc.student_id}")
            s = await session.get(Student, tg_acc.student_id)
            if s:
                print(f"Student Name: {s.full_name}")
                print(f"Student Login: {s.hemis_login}")
                
                # CHECK ACTIVITIES
                act_stmt = select(UserActivity).where(UserActivity.student_id == s.id)
                act_res = await session.execute(act_stmt)
                acts = act_res.scalars().all()
                print(f"\nActivity Count for Student {s.id}: {len(acts)}")
                for a in acts:
                    print(f"[{a.id}] {a.name} ({a.status}) | Created: {a.created_at}")
            else:
                print("Student not found for this TG ID!")
        else:
            print("No TgAccount found for this TG ID!")

        # Also search for students with phone +998906110006 from CSV
        print("\n--- Searching for student by phone from CSV ---")
        # Assuming Student model has a phone field or we search by name again
        # Let's search by name "Muhammadali" again but look at ALL matches
        stmt = select(Student).where(Student.full_name.ilike("%Akramjonov%"))
        result = await session.execute(stmt)
        for s in result.scalars():
             print(f"ID: {s.id} | Name: {s.full_name}")

if __name__ == "__main__":
    asyncio.run(main())

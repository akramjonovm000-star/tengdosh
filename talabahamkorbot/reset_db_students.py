import asyncio
from sqlalchemy import select, delete
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount

async def reset_students():
    async with AsyncSessionLocal() as session:
        print("🚀 Starting Database Reset for Students...")

        # 1. Delete all Student Telegram Accounts (Logout Everyone)
        stmt_tg = delete(TgAccount).where(TgAccount.student_id.isnot(None))
        result_tg = await session.execute(stmt_tg)
        print(f"✅ Logged out {result_tg.rowcount} students (Deleted TgAccounts).")

        # 2. Delete Legacy Students (No HEMIS ID)
        # This forces them to re-register via HEMIS password check
        stmt_stu = delete(Student).where(Student.hemis_id.is_(None))
        result_stu = await session.execute(stmt_stu)
        print(f"🗑️ Deleted {result_stu.rowcount} legacy student records (No HEMIS ID).")

        await session.commit()
        print("✨ Database clean and ready for fresh HEMIS logins!")

if __name__ == "__main__":
    asyncio.run(reset_students())

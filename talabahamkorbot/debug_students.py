from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount

async def check_user():
    async with AsyncSessionLocal() as session:
        tg_id = 8155790902
        acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
        if acc:
            print(f"Found Account: {acc.id}, Role: {acc.current_role}")
            if acc.student_id:
                stu = await session.get(Student, acc.student_id)
                print(f"Linked Student: {stu.id}, Name: {stu.full_name}, HemisID: '{stu.hemis_id}'")
            else:
                print("No Student Linked.")
        else:
            print("No TgAccount found for this user.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_user())

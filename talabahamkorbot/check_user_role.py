
import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount
from sqlalchemy import select

async def check_role():
    async with AsyncSessionLocal() as db:
        acc = await db.scalar(select(TgAccount).where(TgAccount.telegram_id == 7476703866))
        if acc:
            print(f"Account ID: {acc.id}")
            print(f"Role: {acc.current_role}")
            print(f"Student ID: {acc.student_id}")
            print(f"Staff ID: {acc.staff_id}")
        else:
            print("Account not found")

if __name__ == "__main__":
    asyncio.run(check_role())

import asyncio
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student


async def check_user():
    async with AsyncSessionLocal() as session:
        tgy_id = 387178074
        print(f"Checking Telegram ID: {tgy_id}")
        
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tgy_id))
        if not account:
            print("Account not found.")
            return

        print(f"Account found. Student ID: {account.student_id}")
        
        if account.student_id:
            student = await session.get(Student, account.student_id)
            if student:
                print(f"Student: {student.full_name}")
                print(f"Short name: {student.short_name}")
                print(f"Role: {account.current_role}")
            else:
                print("Student record missing!")

if __name__ == "__main__":
    asyncio.run(check_user())

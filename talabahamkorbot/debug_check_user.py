
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student

async def check_user(tg_id: int):
    async with AsyncSessionLocal() as session:
        print(f"Checking for Telegram ID: {tg_id}")
        
        # Check Account
        stmt = select(TgAccount).where(TgAccount.telegram_id == tg_id)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account:
            print(f"✅ TgAccount FOUND! ID: {account.id}")
            print(f"   Student ID: {account.student_id}")
            print(f"   Role: {account.current_role}")
            
            if account.student_id:
                student = await session.get(Student, account.student_id)
                if student:
                    print(f"✅ Student Linked: {student.full_name} ({student.hemis_login})")
                else:
                    print(f"❌ Student ID {account.student_id} not found in Student table!")
            else:
                print("❌ No Student ID linked!")
        else:
            print("❌ TgAccount NOT found.")

if __name__ == "__main__":
    tg_id = 8155790902
    if len(sys.argv) > 1:
        tg_id = int(sys.argv[1])
    asyncio.run(check_user(tg_id))

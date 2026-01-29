import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.grade_checker import send_welcome_report
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

USER_TG_ID = 8155790902 # Replace with a known ID if needed, or query dynamically

async def main():
    print("🚀 Sending Test Welcome Report...")
    async with AsyncSessionLocal() as session:
        stmt = select(TgAccount).where(TgAccount.student_id.is_not(None)).limit(1)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account:
            print(f"Sending to Student ID: {account.student_id} (TG: {account.telegram_id})")
            await send_welcome_report(account.student_id)
            print("✅ Sent!")
        else:
            print("❌ No student found to test.")

if __name__ == "__main__":
    asyncio.run(main())

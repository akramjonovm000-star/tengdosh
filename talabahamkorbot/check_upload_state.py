import asyncio
import sys
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import PendingUpload, TgAccount

async def main():
    session_id = "6687F67D"
    async with AsyncSessionLocal() as db:
        print(f"Checking Session: {session_id}")
        pending = await db.get(PendingUpload, session_id)
        if not pending:
            print("Session not found in DB!")
            return

        print(f"PendingUpload found: student_id={pending.student_id}, file_ids={pending.file_ids}")
        
        tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == pending.student_id))
        if tg_acc:
             print(f"Telegram ID: {tg_acc.telegram_id}")
        else:
             print("Telegram Account not found for student!")

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

async def check():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(TgAccount))
        accs = res.all()
        print(f"Total Accounts: {len(accs)}")
        for a in accs:
            acc = a[0]
            print(f"ID: {acc.id}, TID: {acc.telegram_id}, Staff: {acc.staff_id}, Student: {acc.student_id}, Role: {acc.current_role}")

if __name__ == "__main__":
    asyncio.run(check())

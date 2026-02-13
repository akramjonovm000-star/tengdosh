
import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount

async def check():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(TgAccount).where(TgAccount.id == 172))
        acc = res.scalar_one_or_none()
        if acc:
            print(f'Account 172: telegram_id={acc.telegram_id}, staff_id={acc.staff_id}, student_id={acc.student_id}')

if __name__ == "__main__":
    asyncio.run(check())


import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from database.db_connect import AsyncSessionLocal
from database.models import Student, TgAccount
from sqlalchemy import select, func

async def check():
    session = AsyncSessionLocal()
    total = await session.scalar(select(func.count(Student.id)))
    registered = await session.scalar(select(func.count(TgAccount.student_id)))
    print(f"Total Students: {total}")
    print(f"Registered (Active): {registered}")
    await session.close()

if __name__ == "__main__":
    asyncio.run(check())

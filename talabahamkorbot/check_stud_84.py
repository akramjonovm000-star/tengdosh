import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Student
async def run():
    async with AsyncSessionLocal() as db:
        print(await db.get(Student, 84))
asyncio.run(run())

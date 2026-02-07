import asyncio
from sqlalchemy import update
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def fix():
    async with AsyncSessionLocal() as db:
        await db.execute(update(Student).where(Student.id == 771).values(group_number='DEMO-301'))
        await db.commit()
        print("Updated student 771 to group DEMO-301")

if __name__ == "__main__":
    asyncio.run(fix())

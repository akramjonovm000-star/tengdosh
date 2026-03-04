import asyncio
from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Club
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Club.department).distinct())
        departments = result.scalars().all()
        print("Existing Departments:", departments)
if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/")
    sys.path.append("/home/user/talabahamkor/talabahamkorbot/")
    asyncio.run(main())

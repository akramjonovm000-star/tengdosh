
import asyncio
from sqlalchemy import select
from database.db_connect import get_session
from database.models import Student

async def f():
    async for db in get_session():
        try:
            r = (await db.execute(select(Student.level_name).distinct())).scalars().all()
            with open("levels.log", "w") as f:
                f.write(str(r))
        except Exception as e:
            with open("levels.log", "w") as f:
                f.write(f"Error: {e}")
        break

if __name__ == "__main__":
    asyncio.run(f())

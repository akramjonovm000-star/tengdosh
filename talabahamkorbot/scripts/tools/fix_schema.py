import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import asyncio
from sqlalchemy import text
from database.db_connect import engine, Base
import database.models  # Register models with Base

async def fix_schema():
    async with engine.begin() as conn:
        print("Dropping tutor_groups table...")
        await conn.execute(text("DROP TABLE IF EXISTS tutor_groups CASCADE"))
        print("Recreating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_schema())

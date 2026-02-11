import asyncio
import sys
sys.path.append('/home/user/talabahamkor/talabahamkorbot')
from database.db_connect import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT count(*) FROM pg_stat_activity;"))
        count = res.scalar()
        res = await db.execute(text("SHOW max_connections;"))
        max_conn = res.scalar()
        print(f"Current Connections: {count}")
        print(f"Max Connections: {max_conn}")

if __name__ == "__main__":
    asyncio.run(main())

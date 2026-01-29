import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def list_tables():
    async with engine.connect() as conn:
        print(f"Checking database: {engine.url.database}")
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        tables = [row[0] for row in result.fetchall()]
        print("Existing Tables:")
        for t in sorted(tables):
            print(f"- {t}")

if __name__ == "__main__":
    asyncio.run(list_tables())

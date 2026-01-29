import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def check_schema():
    async with engine.connect() as conn:
        # Check if table exists
        result = await conn.execute(text(
            "SELECT exists(select * from information_schema.tables where table_name = 'tutor_groups')"
        ))
        exists = result.scalar()
        
        if exists:
            print("✅ Table 'tutor_groups' EXISTS.")
            # Check columns
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'tutor_groups'"
            ))
            columns = [row[0] for row in result.fetchall()]
            print(f"   Columns: {columns}")
        else:
            print("❌ Table 'tutor_groups' DOES NOT EXIST.")

if __name__ == "__main__":
    asyncio.run(check_schema())

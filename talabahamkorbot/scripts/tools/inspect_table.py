import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def inspect_table():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT schemaname, tablename, tableowner 
            FROM pg_tables 
            WHERE tablename = 'tutor_groups';
        """))
        row = result.fetchone()
        if row:
            print(f"Schema: {row[0]}, Table: {row[1]}, Owner: {row[2]}")
        else:
            print("Table not found in pg_tables view.")

if __name__ == "__main__":
    asyncio.run(inspect_table())

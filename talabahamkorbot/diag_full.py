import asyncio
import sys
import os
sys.path.append(os.path.abspath("."))
from database.db_connect import engine
from sqlalchemy import text

async def diagnostic_full():
    print("🔍 Comprehensive Database Diagnostic")
    async with engine.connect() as conn:
        for table in ['students', 'users', 'staff']:
            res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            cols = [r[0] for r in res.fetchall()]
            print(f"\n📊 Table: '{table}' ({len(cols)} columns)")
            for c in sorted(cols):
                print(f"  - {c}")

if __name__ == "__main__":
    asyncio.run(diagnostic_full())

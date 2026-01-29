import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def grant_permissions():
    async with engine.begin() as conn:
        # Grant usage on schema
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO public;"))
        # Grant all on tables to public (for debugging visibility)
        await conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO public;"))
        # Also specifically for postgres if needed, but it's superuser
        print("Granted permissions.")

if __name__ == "__main__":
    asyncio.run(grant_permissions())

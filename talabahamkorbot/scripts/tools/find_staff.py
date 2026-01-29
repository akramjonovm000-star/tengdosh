import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import select
from database.db_connect import engine
from database.models import Staff, TgAccount

TG_ID = 2086982893

async def find_staff():
    async with engine.connect() as conn:
        result = await conn.execute(select(Staff).join(TgAccount).where(TgAccount.telegram_id == TG_ID))
        staff = result.fetchone()
        
        if staff:
            print(f"✅ Found Staff: ID={staff.id}, Name={staff.full_name}, Role={staff.role}")
        else:
            print("❌ Staff not found.")

if __name__ == "__main__":
    asyncio.run(find_staff())

import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from sqlalchemy import text
from database.db_connect import engine

async def fix_feedback():
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE student_feedback SET assigned_staff_id = 9 WHERE id = 3;"))
        print("Updated student_feedback ID 3 with assigned_staff_id = 9")

if __name__ == "__main__":
    asyncio.run(fix_feedback())

import asyncio
import sys
from sqlalchemy import select
from database.db_connect import async_session
from database.models import Staff

async def find_staff(name_part):
    async with async_session() as db:
        stmt = select(Staff).where(Staff.full_name.ilike(f"%{name_part}%"))
        result = await db.execute(stmt)
        staffs = result.scalars().all()
        
        if not staffs:
            print(f"No staff found matching '{name_part}'")
            return

        for s in staffs:
            print(f"ID: {s.id} | Name: {s.full_name} | Role: {s.role} | Phone: {s.phone} | HEMIS ID: {s.hemis_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_staff.py <name_part>")
        sys.exit(1)
    asyncio.run(find_staff(sys.argv[1]))

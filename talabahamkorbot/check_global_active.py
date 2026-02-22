import asyncio
import json
from sqlalchemy import select, func, or_
from database.db_connect import get_db
from database.models import Student, Staff, TgAccount, StaffRole, University

async def check_global_active():
    async for db in get_db():
        # Get count of active platform users for universities OTHER than UzJMCU (id=1)
        # Active platform user: last_active_at != None
        
        stmt = select(func.count(Student.id)).where(
            Student.university_id != 1,
            Student.last_active_at != None
        )
        global_active = await db.scalar(stmt)
        
        # Also let's see which universities they belong to
        stmt_detail = select(
            Student.university_name, 
            func.count(Student.id)
        ).where(
            Student.university_id != 1,
            Student.last_active_at != None
        ).group_by(Student.university_name)
        
        details = await db.execute(stmt_detail)
        
        print(f"Global active users (excluding UzJMCU): {global_active}")
        for name, count in details.all():
            print(f"  - {name}: {count}")

if __name__ == '__main__':
    asyncio.run(check_global_active())

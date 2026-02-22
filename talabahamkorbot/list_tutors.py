import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, StaffRole

async def main():
    async with AsyncSessionLocal() as db:
        # Fetch staff with tutor role
        stmt = select(Staff).where(Staff.role.in_([StaffRole.TYUTOR, "tutor"]))
        result = await db.execute(stmt)
        tutors = result.scalars().all()
        
        print(f"Found {len(tutors)} tutors:")
        for t in tutors:
            print(f"- ID: {t.id} | Name: {t.full_name} | Login: {t.username or t.employee_id_number or t.hemis_id} | University: {t.university_id}")
            
if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())

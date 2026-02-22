import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # Check staff with id 80 or username 'dekanat'
        staff1 = await db.scalar(select(Staff).where(Staff.id == 80))
        staff2 = await db.scalar(select(Staff).where(Staff.username == 'dekanat'))
        
        print("Staff id 80:", staff1.full_name if staff1 else "Not found")
        print("Staff username 'dekanat':", staff2.full_name if staff2 else "Not found")

        # Let's see if we can create one
        if not staff1 and not staff2:
            new_staff = Staff(
                full_name="Demo Dekanat",
                role="dekanat",
                username="dekanat",
                employee_id_number="demo.dekanat",
                faculty_id=36,
                university_id=1
            )
            db.add(new_staff)
            await db.commit()
            print("Created demo.dekanat staff account!")
        
if __name__ == "__main__":
    asyncio.run(main())

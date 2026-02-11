import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy.future import select

async def simulate_login():
    async with AsyncSessionLocal() as session:
        print("Simulating demo login for sanjar_botirovich...")
        
        # This is the logic currently in api/auth.py
        role = "rahbariyat"
        
        # Current BUGGY query:
        demo_staff = await session.scalar(
            select(Staff).where(
                (Staff.hemis_id == 999999) | (Staff.jshshir == "12345678901234")
            )
        )
        
        if not demo_staff:
            print("Demo staff NOT found (as expected due to bug).")
            print("Attempting to recreate (this should fail due to unique constraint)...")
            try:
                demo_staff = Staff(
                    full_name="Sanjar Botirovich",
                    jshshir="98765432109876", # This is the unique constraint!
                    role=role,
                    hemis_id=888888,
                    phone="998901234567",
                    university_id=1,
                    university_name="O'zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti"
                )
                session.add(demo_staff)
                await session.commit()
                print("Wait, it succeeded? That shouldn't happen if the record already exists.")
            except Exception as e:
                print(f"Caught expected exception: {type(e).__name__}: {str(e)}")
        else:
            print(f"Found existing staff: {demo_staff.full_name}, ID={demo_staff.id}, Role={demo_staff.role}")

if __name__ == "__main__":
    asyncio.run(simulate_login())

import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy.future import select

async def simulate_login_fixed():
    async with AsyncSessionLocal() as session:
        print("Simulating FIXED demo login for sanjar_botirovich...")
        
        role = "rahbariyat"
        
        # This is the logic I just implemented in api/auth.py
        target_hemis_id = 999999 if role == "tutor" else 888888
        target_jshshir = "12345678901234" if role == "tutor" else "98765432109876"

        demo_staff = await session.scalar(
            select(Staff).where(
                (Staff.hemis_id == target_hemis_id) | (Staff.jshshir == target_jshshir)
            )
        )
        
        if not demo_staff:
            print("Demo staff NOT found. Creating...")
            demo_staff = Staff(
                full_name="Sanjar Botirovich",
                jshshir=target_jshshir,
                role=role,
                hemis_id=target_hemis_id,
                phone="998901234567",
                university_id=1
            )
            session.add(demo_staff)
            await session.commit()
            print("Successfully created demo staff.")
        else:
            print(f"SUCCESS: Found existing staff: {demo_staff.full_name}, ID={demo_staff.id}, Role={demo_staff.role}")

if __name__ == "__main__":
    asyncio.run(simulate_login_fixed())

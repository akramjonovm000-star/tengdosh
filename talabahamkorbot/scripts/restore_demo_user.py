import asyncio
from database.db_connect import AsyncSessionLocal
from database.models import Staff
from sqlalchemy.future import select
from datetime import datetime, timedelta

async def restore_demo():
    async with AsyncSessionLocal() as session:
        print("Restoring demo account 'sanjar_botirovich'...")
        
        # Find staff by hemis_id 888888
        f_query = select(Staff).where(Staff.hemis_id == 888888)
        f_res = await session.execute(f_query)
        sf = f_res.scalar_one_or_none()
        
        if sf:
            print(f"Updating Staff ID: {sf.id}")
            sf.is_premium = True
            sf.premium_expiry = datetime.utcnow() + timedelta(days=365)
            sf.role = "rahbariyat"
            sf.ai_limit = 1000
            sf.is_active = True
            await session.commit()
            print("Successfully updated staff record.")
        else:
            print("Staff record not found! Creating new demo staff...")
            new_staff = Staff(
                full_name="Sanjar Botirovich",
                jshshir="98765432109876",
                role="rahbariyat",
                hemis_id=888888,
                phone="998901234567",
                university_id=1,
                university_name="O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti",
                is_premium=True,
                premium_expiry=datetime.utcnow() + timedelta(days=365),
                ai_limit=1000
            )
            session.add(new_staff)
            await session.commit()
            print("Successfully created new staff demo record.")

if __name__ == "__main__":
    asyncio.run(restore_demo())

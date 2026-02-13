
import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Staff, StaffRole, Student

async def fix():
    async with AsyncSessionLocal() as s:
        async with s.begin():
            tid = 7476703866
            print(f"🚀 Fixing Account for TID {tid}...")
            
            # 1. Ensure Staff 27 is DEVELOPER
            res = await s.execute(select(Staff).where(Staff.id == 27))
            st = res.scalar_one_or_none()
            if not st:
                print("⚠️ Staff 27 not found, searching for RAHIMXONOV...")
                res = await s.execute(select(Staff).where(Staff.full_name.ilike('%RAHIMXONOV%')))
                st = res.scalars().first()
            
            if st:
                print(f"✅ Found Staff {st.id}, setting role to DEVELOPER")
                st.role = StaffRole.DEVELOPER
                st.is_active = True
                staff_id = st.id
            else:
                print("❌ No Staff found. Creating one...")
                st = Staff(full_name="RAHIMXONOV JAVOHIRXON", role=StaffRole.DEVELOPER, is_active=True)
                s.add(st)
                await s.flush()
                staff_id = st.id

            # 2. Update Account 246
            res = await s.execute(select(TgAccount).where(TgAccount.telegram_id == tid))
            acc = res.scalar_one_or_none()
            if acc:
                print(f"✅ Found Account {acc.id}, linking to Staff {staff_id} and setting role...")
                acc.staff_id = staff_id
                acc.current_role = StaffRole.DEVELOPER.value
            else:
                print("❌ Account not found. Creating new...")
                acc = TgAccount(telegram_id=tid, staff_id=staff_id, current_role=StaffRole.DEVELOPER.value)
                s.add(acc)
            
            print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(fix())

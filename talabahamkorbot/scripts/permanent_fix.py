
import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Staff, StaffRole

async def fix():
    async with AsyncSessionLocal() as s:
        async with s.begin():
            tid = 7476703866
            print(f"🚀 Fixing Account for TID {tid}...")
            
            # Find the account
            res = await s.execute(select(TgAccount).where(TgAccount.telegram_id == tid))
            acc = res.scalar_one_or_none()
            
            if acc:
                print(f"✅ Found Account {acc.id}")
                acc.staff_id = 27
                acc.current_role = StaffRole.DEVELOPER.value
                print(f"✅ Linked to Staff 27 and set role to {StaffRole.DEVELOPER.value}")
            else:
                print(f"❌ Account for TID {tid} not found. Creating new...")
                acc = TgAccount(telegram_id=tid, staff_id=27, current_role=StaffRole.DEVELOPER.value)
                s.add(acc)
            
            # Verify Staff 27
            res = await s.execute(select(Staff).where(Staff.id == 27))
            st = res.scalar_one_or_none()
            if st:
                st.role = StaffRole.DEVELOPER
                st.is_active = True
                print(f"✅ Verified Staff 27 is DEVELOPER and active")
            
            print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(fix())

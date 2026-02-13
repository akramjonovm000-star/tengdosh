
import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import Staff, StaffRole, TgAccount

async def make_developer(telegram_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Find the TgAccount
            res = await session.execute(select(TgAccount).where(TgAccount.telegram_id == telegram_id))
            account = res.scalar_one_or_none()
            
            if not account:
                print(f"❌ No TgAccount found for {telegram_id}")
                return

            if not account.staff_id:
                # Need to link to a Staff entry. Let's see if one exists for this user
                # If not, we might need to create one, but usually admins are already in Staff.
                # Since the user asked to "add to admin", we'll ensure they have a Staff entry with the role.
                print(f"ℹ️ Account {telegram_id} has no staff link. Checking for existing staff...")
                res = await session.execute(select(Staff).where(Staff.telegram_id == telegram_id))
                staff = res.scalar_one_or_none()
                
                if not staff:
                    print(f"🆕 Creating new Staff entry for {telegram_id}...")
                    staff = Staff(
                        full_name="Admin", # Generic name, will be updated by bot later
                        role=StaffRole.DEVELOPER,
                        telegram_id=telegram_id,
                        is_active=True
                    )
                    session.add(staff)
                    await session.flush()
                else:
                    print(f"✅ Found existing staff {staff.id}, updating role...")
                    staff.role = StaffRole.DEVELOPER
                
                account.staff_id = staff.id
            else:
                # Update existing staff
                print(f"✅ Updating existing staff {account.staff_id} to DEVELOPER role...")
                await session.execute(
                    update(Staff)
                    .where(Staff.id == account.staff_id)
                    .values(role=StaffRole.DEVELOPER, is_active=True)
                )
            
            # Also update current_role in TgAccount for immediate effect
            account.current_role = StaffRole.DEVELOPER.value
            
            print(f"🚀 Success! User {telegram_id} is now an admin (DEVELOPER).")

if __name__ == "__main__":
    asyncio.run(make_developer(7476703866))

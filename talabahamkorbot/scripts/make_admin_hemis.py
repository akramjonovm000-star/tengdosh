
import asyncio
from sqlalchemy import select, update
from database.db_connect import AsyncSessionLocal
from database.models import Staff, StaffRole, Student, TgAccount

async def make_admin_by_hemis(identifier: str):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            print(f"🔍 Searching for user with HEMIS ID or Login: {identifier}")
            
            # --- 1. SEARCH STUDENT ---
            res = await session.execute(
                select(Student).where(
                    (Student.hemis_id == identifier) | (Student.hemis_login == identifier)
                )
            )
            student = res.scalar_one_or_none()
            
            # --- 2. SEARCH STAFF ---
            staff = None
            if student:
                # If student found, search staff by their linked ID or name
                res = await session.execute(select(Staff).where(Staff.full_name == student.full_name))
                staff = res.scalar_one_or_none()
            else:
                # If no student, try staff directly by numeric id if applicable
                if identifier.isdigit() and len(identifier) < 10:
                    res = await session.execute(select(Staff).where(Staff.hemis_id == int(identifier)))
                    staff = res.scalar_one_or_none()

            # --- 3. APPLY PROMOTION ---
            if staff:
                print(f"✅ Found Staff entry {staff.id}, updating to DEVELOPER role...")
                staff.role = StaffRole.DEVELOPER
                staff.is_active = True
                
                # Update related TgAccount role if exists
                await session.execute(
                    update(TgAccount)
                    .where(TgAccount.staff_id == staff.id)
                    .values(current_role=StaffRole.DEVELOPER.value)
                )
                print(f"🚀 Success! Staff user is now an admin.")
            elif student:
                print(f"ℹ️ Found Student {student.full_name}. Creating Staff entry for admin access...")
                
                # Check if they have a TgAccount to link
                res = await session.execute(select(TgAccount).where(Student.id == student.id))
                account = res.scalars().first()
                
                staff = Staff(
                    full_name=student.full_name,
                    role=StaffRole.DEVELOPER,
                    telegram_id=account.telegram_id if account else None,
                    hemis_id=int(student.hemis_id) if student.hemis_id and student.hemis_id.isdigit() else None,
                    is_active=True
                )
                session.add(staff)
                await session.flush()
                
                if account:
                    account.staff_id = staff.id
                    account.current_role = StaffRole.DEVELOPER.value
                
                print(f"🚀 Success! Student {student.full_name} now has admin access via new Staff entry.")
            else:
                print(f"❌ User with '{identifier}' not found as Student or Staff.")

if __name__ == "__main__":
    import sys
    target_id = "395251101397"
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    asyncio.run(make_admin_by_hemis(target_id))

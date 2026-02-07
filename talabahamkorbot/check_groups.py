import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup

async def main():
    async with AsyncSessionLocal() as session:
        staff_id = 62 # The Owner
        print(f"--- Checking groups for Staff ID: {staff_id} ---")
        stmt = select(TutorGroup).where(TutorGroup.tutor_id == staff_id)
        result = await session.execute(stmt)
        groups = result.scalars().all()
        print(f"Group count: {len(groups)}")
        for g in groups:
            print(f"Group: {g.group_number}")

        # check if there are ANY groups
        stmt_all = select(TutorGroup)
        res_all = await session.execute(stmt_all)
        all_groups = res_all.scalars().all()
        print(f"\nTotal groups in system: {len(all_groups)}")

if __name__ == "__main__":
    asyncio.run(main())

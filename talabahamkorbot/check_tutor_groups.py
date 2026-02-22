import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup

async def main():
    async with AsyncSessionLocal() as db:
        # Check tyutor1 demo account
        tutor_id = 84
        groups_result = await db.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor_id))
        groups = groups_result.scalars().all()
        print(f"Demo tutor ID 84 groups: {[g.group_number for g in groups]}")

        # Check Maxmanazarov
        tutor_id = 74
        groups_result2 = await db.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor_id))
        groups2 = groups_result2.scalars().all()
        print(f"Maxmanazarov tutor ID 74 groups: {[g.group_number for g in groups2]}")
        
if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())

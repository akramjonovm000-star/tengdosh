import asyncio
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student

async def grant_admin(identifier: str):
    async with AsyncSessionLocal() as session:
        # Search by full name or hemis_login
        stmt = select(Student).where(
            (Student.full_name.ilike(f"%{identifier}%")) | 
            (Student.hemis_login == identifier)
        )
        student = await session.scalar(stmt)
        
        if not student:
            print(f"User '{identifier}' not found.")
            return

        student.is_election_admin = True
        await session.commit()
        print(f"✅ Success: {student.full_name} is now an election admin.")

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Jamolova Shabnam"
    asyncio.run(grant_admin(name))

import asyncio
import sys
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, ChoyxonaComment

async def main():
    async with AsyncSessionLocal() as db:
        print("Checking Students with name 'Javohirxon Rahimxonov'...")
        # Search by partial or full match
        stmt = select(Student).where(Student.full_name.ilike("%Javohirxon%"))
        result = await db.execute(stmt)
        students = result.scalars().all()
        
        for s in students:
            print(f"ID: {s.id}, FullName: {s.full_name}, Username: '{s.username}', HemisLogin: {s.hemis_login}")
            
        print("\nChecking Comments by these students...")
        for s in students:
            comments = await db.execute(select(ChoyxonaComment).where(ChoyxonaComment.student_id == s.id))
            cmts = comments.scalars().all()
            print(f"Student {s.id} has {len(cmts)} comments.")
            if cmts:
                print(f"Example Comment ID: {cmts[0].id}")

if __name__ == "__main__":
    asyncio.run(main())

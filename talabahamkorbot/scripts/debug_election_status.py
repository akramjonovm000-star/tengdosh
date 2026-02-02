import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'talabahamkorbot'))

from sqlalchemy import select
from talabahamkorbot.database.db_connect import AsyncSessionLocal
from talabahamkorbot.database.models import Student, University, Election, TgAccount
from talabahamkorbot.utils.student_utils import get_election_info

async def debug_election_status():
    async with AsyncSessionLocal() as session:
        # Get all students who have a Telegram account (likely the ones testing)
        stmt = select(Student).join(TgAccount).limit(5)
        students = await session.scalars(stmt)
        
        print("--- Debugging Election Status for active students ---")
        for student in students:
            is_admin, has_active = await get_election_info(student, session)
            univ = await session.get(University, student.university_id) if student.university_id else None
            univ_name = univ.name if univ else "None"
            
            print(f"Student: {student.full_name} (ID: {student.id})")
            print(f"  University: {univ_name} (ID: {student.university_id})")
            print(f"  Is Admin: {is_admin}, Has Active Election: {has_active}")
            
            if has_active:
                # Find the election
                active_election = await session.scalar(
                    select(Election).where(
                        Election.university_id == student.university_id,
                        Election.status == "active"
                    )
                )
                if active_election:
                    print(f"  Election Found: {active_election.title} (ID: {active_election.id}, Status: {active_election.status})")
                else:
                    print("  WARNING: get_election_info returned True but no active election found in second query!")
            print("-" * 30)

        # Check all active elections
        print("\n--- All Active Elections in DB ---")
        active_elections = await session.scalars(
            select(Election).where(Election.status == "active")
        )
        for e in active_elections:
            print(f"Election: {e.title} (ID: {e.id}, University ID: {e.university_id}, Deadline: {e.deadline})")

if __name__ == "__main__":
    asyncio.run(debug_election_status())

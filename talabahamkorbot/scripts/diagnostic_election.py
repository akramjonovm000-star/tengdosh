import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append("/home/user/talabahamkor/talabahamkorbot")

from database.db_connect import AsyncSessionLocal
from database.models import Student, Election, ElectionCandidate, ElectionVote
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

async def test():
    async with AsyncSessionLocal() as session:
        # Test student 730, election 6
        election_id = 6
        student_id = 730
        
        print(f"--- Testing Election {election_id} for Student {student_id} ---")
        
        student = await session.get(Student, student_id)
        if not student:
            print(f"Student {student_id} not found!")
            return
            
        print(f"Student: {student.full_name}, Univ: {student.university_id}")
        
        try:
            print("Loading election...")
            # Using the nested selectinload
            election = await session.scalar(
                select(Election)
                .where(
                    and_(
                        Election.id == election_id,
                        Election.university_id == student.university_id
                    )
                )
                .options(
                    selectinload(Election.candidates).selectinload(ElectionCandidate.student),
                    selectinload(Election.candidates).selectinload(ElectionCandidate.faculty)
                )
            )
            
            if not election:
                print("Election not found!")
                # check all elections
                all_elections = await session.scalars(select(Election))
                print("\nOther elections in DB:")
                for e in all_elections:
                    print(f"  ID={e.id}, Univ={e.university_id}, Status={e.status}, Title={e.title}")
                return

            print(f"Election found: {election.title}")
            print(f"Candidates count: {len(election.candidates)}")
            
            for cand in election.candidates:
                print(f"  Candidate {cand.id}:")
                print(f"    Student: {cand.student.full_name if cand.student else 'NONE'}")
                print(f"    Faculty: {cand.faculty.name if cand.faculty else 'NONE'}")
                
            print("\n--- Diagnostic SUCCESS: Code works with data ---")
        except Exception as e:
            import traceback
            print(f"\n--- Diagnostic FAILED ---")
            print(f"Error: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test())

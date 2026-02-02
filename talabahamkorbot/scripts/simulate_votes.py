import asyncio
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import Student, ElectionCandidate, ElectionVote, Election

async def simulate_votes():
    async with AsyncSessionLocal() as session:
        # Get active election
        election = await session.scalar(select(Election).where(Election.is_active == True).limit(1))
        if not election:
            print("No active election found.")
            return

        # Get candidates
        stmt = select(ElectionCandidate).where(ElectionCandidate.election_id == election.id)
        candidates = (await session.scalars(stmt)).all()
        if not candidates:
            print("No candidates found.")
            return

        # Get all students in the same faculty as candidates
        fac_id = candidates[0].faculty_id
        student_stmt = select(Student).where(Student.faculty_id == fac_id)
        students = (await session.scalars(student_stmt)).all()

        print(f"Simulating votes for Election: {election.title}")
        
        # Simple simulation: each student votes for a random candidate
        import random
        votes_count = 0
        for student in students:
            # Check if already voted
            check_stmt = select(ElectionVote).where(
                and_(ElectionVote.election_id == election.id, ElectionVote.voter_id == student.id)
            )
            already_voted = await session.scalar(check_stmt)
            
            if not already_voted:
                target_cand = random.choice(candidates)
                vote = ElectionVote(
                    election_id=election.id,
                    voter_id=student.id,
                    candidate_id=target_cand.id
                )
                session.add(vote)
                votes_count += 1
        
        await session.commit()
        print(f"Successfully simulated {votes_count} votes.")

if __name__ == "__main__":
    asyncio.run(simulate_votes())

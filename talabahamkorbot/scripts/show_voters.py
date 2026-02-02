import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import ElectionVote, Student, ElectionCandidate, Election

async def show_voters():
    async with AsyncSessionLocal() as session:
        # Get current active election
        election = await session.scalar(select(Election).where(Election.is_active == True).limit(1))
        if not election:
            print("❌ Faol saylov topilmadi.")
            return

        print(f"🗳 Saylov: {election.title}")
        print("-" * 50)

        # Get votes with joins
        stmt = select(ElectionVote).options(
            selectinload(ElectionVote.voter),
            selectinload(ElectionVote.candidate).selectinload(ElectionCandidate.student)
        ).where(ElectionVote.election_id == election.id).order_by(ElectionVote.created_at.desc())

        result = await session.execute(stmt)
        votes = result.scalars().all()

        if not votes:
            print("ℹ️ Hozircha hech kim ovoz bermadi.")
            return

        print(f"{'№':<4} | {'Talaba (Kim ovoz berdi)':<30} | {'Nomzod (Kimg otaov boildi)':<30}")
        print("-" * 70)
        for i, v in enumerate(votes, 1):
            voter_name = v.voter.full_name if v.voter else "Noma'lum"
            cand_name = v.candidate.student.full_name if v.candidate and v.candidate.student else "Noma'lum"
            print(f"{i:<4} | {voter_name[:30]:<30} | {cand_name[:30]:<30}")
        
        print("-" * 70)
        print(f"Jami ovozlar: {len(votes)}")

if __name__ == "__main__":
    asyncio.run(show_voters())

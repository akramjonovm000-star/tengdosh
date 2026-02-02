from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from api.dependencies import get_current_student, get_db
from api.schemas import ElectionDetailSchema, ElectionCandidateSchema, ElectionVoteRequestSchema
from database.models import Student, Election, ElectionCandidate, ElectionVote

router = APIRouter()

@router.get("/{election_id}", response_model=ElectionDetailSchema)
async def get_election_details(
    election_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific election including candidates.
    Matches logic from bot's show_election_main.
    """
    election = await db.scalar(
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
        raise HTTPException(status_code=404, detail="Saylov topilmadi")

    # Check if student already voted
    voted = await db.scalar(
        select(ElectionVote).where(
            and_(
                ElectionVote.election_id == election_id,
                ElectionVote.voter_id == student.id
            )
        )
    )

    # Convert to schema
    candidate_schemas = []
    for cand in election.candidates:
        candidate_schemas.append(ElectionCandidateSchema(
            id=cand.id,
            full_name=cand.student.full_name,
            faculty_name=cand.faculty.name,
            campaign_text=cand.campaign_text,
            image_url=cand.photo_id, # In bot this might be file_id, for app we might need URL later
            order=cand.order
        ))

    return ElectionDetailSchema(
        id=election.id,
        title=election.title,
        description=election.description,
        deadline=election.deadline,
        has_voted=voted is not None,
        voted_candidate_id=voted.candidate_id if voted else None,
        candidates=candidate_schemas
    )

@router.post("/{election_id}/vote")
async def vote_in_election(
    election_id: int,
    req: ElectionVoteRequestSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a vote for a candidate.
    Enforces cross-platform one-vote rule via DB unique constraint.
    """
    # 1. Verify election exists and is active
    election = await db.get(Election, election_id)
    if not election or election.status != "active":
        raise HTTPException(status_code=400, detail="Saylov faol emas")

    # 2. Verify candidate belongs to this election
    candidate = await db.get(ElectionCandidate, req.candidate_id)
    if not candidate or candidate.election_id != election_id:
        raise HTTPException(status_code=400, detail="Nomzod topilmadi")

    # 3. Create vote
    # UniqueConstraint(election_id, voter_id) will raise IntegrityError if already voted
    from sqlalchemy.exc import IntegrityError
    
    new_vote = ElectionVote(
        election_id=election_id,
        voter_id=student.id,
        candidate_id=req.candidate_id
    )
    db.add(new_vote)
    
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Siz ushbu saylovda ovoz berib bo'lgansiz")

    return {"status": "success", "message": "Ovozingiz qabul qilindi"}

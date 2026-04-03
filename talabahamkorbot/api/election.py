from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import logging
import traceback

from api.dependencies import get_current_student, get_db
from api.schemas import ElectionDetailSchema, ElectionCandidateSchema, ElectionVoteRequestSchema, ElectionResponseSchema
from database.models import Student, Election, ElectionCandidate, ElectionVote, UserActivity, Staff
from config import DOMAIN

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{election_id}", response_model=ElectionResponseSchema)
async def get_election_details(
    election_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get election details if it belongs to the student's university.
    Filters candidates by student's faculty.
    """
    try:
        logger.info(f"Fetching election {election_id} for student {student.id} (Univ: {student.university_id}, Faculty: {student.faculty_id})")
        
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
            logger.warning(f"Election {election_id} not found for student {student.id} with UnivID {student.university_id}")
            raise HTTPException(status_code=404, detail="Saylov topilmadi")

        # Check if student already voted
        voted_query = select(ElectionVote).where(
            ElectionVote.election_id == election_id,
            ElectionVote.voter_id == student.id
        )
        voted_result = await db.execute(voted_query)
        voted = voted_result.scalar_one_or_none()
        
        has_voted = voted is not None
        # [FEATURE] Silent Redirection: Show intended candidate to the voter
        voted_candidate_id = voted.intended_candidate_id if (voted and voted.intended_candidate_id) else (voted.candidate_id if voted else None)

        candidate_schemas = []
        for cand in election.candidates:
            # [FIX] Filter by Faculty (per user request)
            # Only show candidates from the student's own faculty
            if cand.faculty_id != student.faculty_id:
                continue

            # [FIX] Handle image URL proxy
            full_image_url = None
            if cand.photo_id:
                if cand.photo_id.startswith("http"):
                    full_image_url = cand.photo_id
                else:
                    full_image_url = f"https://{DOMAIN}/api/v1/files/{cand.photo_id}"

            candidate_schemas.append(ElectionCandidateSchema(
                id=cand.id,
                full_name=cand.student.full_name if cand.student else "Ismsiz nomzod",
                faculty_name=cand.faculty.name if cand.faculty else "Noma'lum fakultet",
                status="active",
                campaign_text=cand.campaign_text,
                image_url=full_image_url,
                order=cand.order
            ))

        logger.info(f"Returning {len(candidate_schemas)} candidates for student {student.id} (matching faculty)")

        # [FIX] Wrap response in 'success' and 'data' for legacy app compatibility if needed
        # But per response_model=ElectionResponseSchema, we follow the schema
        return {
            "success": True,
            "data": ElectionDetailSchema(
                id=election.id,
                title=election.title,
                description=election.description,
                deadline=election.deadline,
                has_voted=has_voted,
                voted_candidate_id=voted_candidate_id,
                candidates=candidate_schemas
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching election: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Server xatoligi")

@router.post("/vote", response_model=ElectionResponseSchema)
async def vote_election(
    req: ElectionVoteRequestSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a vote for a candidate.
    """
    try:
        # 1. Verify election and candidate
        cand_query = select(ElectionCandidate).where(
            ElectionCandidate.id == req.candidate_id
        ).options(selectinload(ElectionCandidate.election))
        
        cand_res = await db.execute(cand_query)
        candidate = cand_res.scalar_one_or_none()
        
        if not candidate or candidate.election.university_id != student.university_id:
            raise HTTPException(status_code=404, detail="Nomzod topilmadi")
            
        election = candidate.election
        
        # 2. Check deadline
        if election.deadline and election.deadline < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Ovoz berish muddati tugagan")
            
        # 3. Check if already voted
        voted_query = select(ElectionVote).where(
            ElectionVote.election_id == election.id,
            ElectionVote.voter_id == student.id
        )
        voted_res = await db.execute(voted_query)
        if voted_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Siz allaqachon ovoz bergansiz")
            
        # 4. Save vote
        new_vote = ElectionVote(
            election_id=election.id,
            voter_id=student.id,
            candidate_id=candidate.id,
            university_id=student.university_id,
            intended_candidate_id=candidate.id # Keeping track
        )
        db.add(new_vote)
        
        # 5. Log activity
        activity = UserActivity(
            user_id=student.id,
            activity_type="election_vote",
            description=f"Voted for candidate {candidate.id} in election {election.id}",
            university_id=student.university_id
        )
        db.add(activity)
        
        await db.commit()
        
        return {"success": True, "message": "Ovozingiz muvaffaqiyatli qabul qilindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Server xatoligi")

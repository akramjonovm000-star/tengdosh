from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from api.dependencies import get_current_student, get_db
from api.schemas import ClubSchema, ClubMembershipSchema
from database.models import Student, Club, ClubMembership

router = APIRouter()

class JoinClubRequest(BaseModel):
    club_id: int

@router.get("/my", response_model=List[ClubMembershipSchema])
async def get_my_clubs(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """List clubs the student has joined."""
    memberships = await db.scalars(
        select(ClubMembership)
        .where(ClubMembership.student_id == student.id)
        .options(selectinload(ClubMembership.club))
    )
    return memberships.all()

@router.get("/all", response_model=List[ClubSchema])
async def get_all_clubs(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """List all available clubs with member counts."""
    from sqlalchemy import func
    
    # Subquery for member counts
    subq = (
        select(ClubMembership.club_id, func.count(ClubMembership.id).label('member_count'))
        .group_by(ClubMembership.club_id)
        .subquery()
    )
    
    # Subquery for current user's memberships
    my_subq = (
        select(ClubMembership.club_id)
        .where(ClubMembership.student_id == student.id)
        .subquery()
    )
    
    query = (
        select(
            Club, 
            func.coalesce(subq.c.member_count, 0).label('members_count'),
            (my_subq.c.club_id != None).label('is_joined')
        )
        .outerjoin(subq, Club.id == subq.c.club_id)
        .outerjoin(my_subq, Club.id == my_subq.c.club_id)
    )
    
    result = await db.execute(query)
    
    clubs_data = []
    for club, members_count, is_joined in result.all():
        data = ClubSchema.from_orm(club)
        data.members_count = members_count
        data.is_joined = is_joined
        clubs_data.append(data)
        
    return clubs_data

@router.post("/join")
async def join_club(
    req: JoinClubRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a club.
    In a real scenario, we should verify Telegram Channel subscription.
    For now, we trust the client (or verify later).
    """
    # Check if already a member
    existing = await db.scalar(
        select(ClubMembership)
        .where(
            ClubMembership.student_id == student.id,
            ClubMembership.club_id == req.club_id
        )
    )
    if existing:
        return {"status": "already_joined", "message": "Siz allaqachon a'zosiz"}
    
    # Check if club exists
    club = await db.get(Club, req.club_id)
    if not club:
         raise HTTPException(status_code=404, detail="Club not found")

    membership = ClubMembership(
        student_id=student.id,
        club_id=req.club_id
    )
    db.add(membership)
    await db.commit()
    
    return {"status": "success", "message": "Muvaffaqiyatli a'zo bo'ldingiz"}

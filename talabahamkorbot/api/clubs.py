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
    """List all available clubs."""
    clubs = await db.scalars(select(Club))
    return clubs.all()

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

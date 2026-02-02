from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.dependencies import get_current_student, get_db
from api.schemas import StudentDashboardSchema
from database.models import Student, UserActivity, ClubMembership, Election

router = APIRouter()

from typing import Optional
from services.sync_service import sync_student_data
from utils.student_utils import get_election_info
from sqlalchemy import and_
from datetime import datetime

@router.get("/", response_model=StudentDashboardSchema)
async def get_dashboard_stats(
    refresh: Optional[bool] = False,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for the student dashboard.
    """
    if refresh:
        from services.sync_service import sync_student_data
        await sync_student_data(db, student.id)
        await db.commit() # Ensure changes are saved!
        # Re-fetch student to get updated values
        await db.refresh(student)
    
    # 1. Activities Count
    activities_count = await db.scalar(
        select(func.count(UserActivity.id))
        .where(UserActivity.student_id == student.id)
    ) or 0
    
    # 2. Approved Activities Count
    approved_count = await db.scalar(
        select(func.count(UserActivity.id))
        .where(
            UserActivity.student_id == student.id, 
            UserActivity.status == 'approved'
        )
    ) or 0
    
    # 3. Clubs Count
    clubs_count = await db.scalar(
        select(func.count(ClubMembership.id))
        .where(ClubMembership.student_id == student.id)
    ) or 0
    
    # 4. GPA & Absence (Use stored data as primary source for speed)
    gpa = student.gpa or 0.0
    missed_total = student.missed_hours or 0
    missed_excused = student.missed_hours_excused or 0
    missed_unexcused = student.missed_hours_unexcused or 0
    
    # Extra safety sync for Jami logic
    if missed_total < (missed_excused + missed_unexcused):
        missed_total = missed_excused + missed_unexcused
    
    # Optional: If data is 0 or very old, user can trigger refresh via mobile app pull-to-refresh
    # For now, we trust the background sync.
    
    # 5. Election Info
    _, has_active_election = await get_election_info(student, db)
    active_election_id = None
    if has_active_election:
        active_election = await db.scalar(
            select(Election).where(
                and_(
                    Election.university_id == student.university_id,
                    Election.status == "active"
                )
            ).order_by(Election.created_at.desc())
        )
        if active_election:
            active_election_id = active_election.id

    return StudentDashboardSchema(
        gpa=gpa,
        missed_hours=missed_total,
        missed_hours_excused=missed_excused,
        missed_hours_unexcused=missed_unexcused,
        activities_count=activities_count,
        clubs_count=clubs_count,
        activities_approved_count=approved_count,
        has_active_election=has_active_election,
        active_election_id=active_election_id
    )

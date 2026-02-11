from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database.db_connect import get_db
from database.models import Student, Staff, UserActivity, Faculty
from api.dependencies import get_current_staff

router = APIRouter()

# ============================================================
# DASHBOARD SCHEMAS
# ============================================================
from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_activities: int
    pending_count: int
    approved_count: int
    rejected_count: int
    activities_this_month: int
    category_breakdown: Dict[str, int]
    
class RecentSubmissionItem(BaseModel):
    id: int
    student_name: str
    faculty_name: Optional[str]
    category: str
    name: str
    date: str
    status: str
    created_at: datetime

# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get KPI stats for Social Activities (UserActivity).
    """
    if staff.role not in ['rahbariyat', 'owner', 'developer', 'rektor', 'prorektor', 'dekanat', 'tyutor']:
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    # Base query
    base_query = select(UserActivity)
    
    # Context filtering (Dekanat/Tyutor see only their scope)
    # For now, we assume Dashboard shows GLOBAL stats for Rahbariyat.
    # If Dekanat calls this, we might want to filter, but let's keep it simple for now.

    # 1. Total Activity Count (All time)
    total_activities = await db.scalar(select(func.count(UserActivity.id))) or 0
    
    # 2. Status Counts
    # Use separate queries or group by for efficiency. Group by is better.
    status_counts_res = await db.execute(
        select(UserActivity.status, func.count(UserActivity.id))
        .group_by(UserActivity.status)
    )
    status_map = {r[0]: r[1] for r in status_counts_res.all()}
    
    pending_count = status_map.get("pending", 0)
    # "confirmed" or "approved" - check model usage. Handlers use "confirmed".
    approved_count = status_map.get("confirmed", 0) 
    rejected_count = status_map.get("rejected", 0)

    # 3. Activities this month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    activities_this_month = await db.scalar(
        select(func.count(UserActivity.id)).where(UserActivity.created_at >= start_of_month)
    ) or 0
    
    # 4. Category Breakdown
    cat_counts_res = await db.execute(
        select(UserActivity.category, func.count(UserActivity.id))
        .group_by(UserActivity.category)
    )
    category_breakdown = {r[0]: r[1] for r in cat_counts_res.all()}

    return {
        "total_activities": total_activities,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "activities_this_month": activities_this_month,
        "category_breakdown": category_breakdown
    }

@router.get("/recent-submissions", response_model=List[RecentSubmissionItem])
async def get_recent_submissions(
    limit: int = 10,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest submitted activities.
    """
    stmt = (
        select(UserActivity)
        .options(selectinload(UserActivity.student)) # Eager load student
        .order_by(desc(UserActivity.created_at))
        .limit(limit)
    )
    
    results = await db.scalars(stmt)
    items = []
    
    for act in results.all():
        student_name = "Unknown"
        faculty_name = None
        if act.student:
            student_name = act.student.full_name
            faculty_name = act.student.faculty_name
            
        items.append({
            "id": act.id,
            "student_name": student_name,
            "faculty_name": faculty_name,
            "category": act.category,
            "name": act.name,
            "date": act.date or "",
            "status": act.status,
            "created_at": act.created_at
        })
        
    return items

@router.get("/faculties", response_model=List[dict])
async def get_faculty_activity_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity stats per faculty (based on UserActivity).
    """
    # 1. Get Faculties
    faculties = (await db.execute(select(Faculty))).scalars().all()
    stats = []
    
    for f in faculties:
        # Count activities linked to students of this faculty
        # Join UserActivity -> Student -> Faculty
        count = await db.scalar(
            select(func.count(UserActivity.id))
            .join(Student, UserActivity.student_id == Student.id)
            .where(Student.faculty_id == f.id)
        ) or 0
        
        stats.append({
            "id": f.id,
            "name": f.name,
            "activity_count": count
        })
        
    stats.sort(key=lambda x: x['activity_count'], reverse=True)
    return stats
    
# Import selectinload for lazy loading
from sqlalchemy.orm import selectinload

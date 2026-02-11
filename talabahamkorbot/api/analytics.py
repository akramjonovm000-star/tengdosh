from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from database.db_connect import get_db
from database.models import Student, Staff, ActivityLog, ActivityType, Faculty
from api.dependencies import get_current_staff
from services.activity_service import ActivityService

router = APIRouter()

# ============================================================
# DASHBOARD SCHEMAS
# ============================================================
from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_students: int
    active_students_7d: int
    active_percentage: float
    total_activities_today: int
    top_faculty: Optional[str] = None
    
class ActivityTrendItem(BaseModel):
    date: str
    count: int

class FacultyActivityItem(BaseModel):
    id: int
    name: str
    activity_count: int
    student_count: int
    avg_activity: float

class StudentActivityItem(BaseModel):
    id: int
    full_name: str
    faculty_name: Optional[str]
    image_url: Optional[str]
    total_activity_count: int
    last_active_at: Optional[datetime]
    status: str # 'High', 'Medium', 'Low', 'Inactive'

# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get high-level KPI stats for the dashboard.
    """
    if staff.role not in ['rahbariyat', 'owner', 'developer', 'rektor', 'prorektor']:
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    # 1. Total Students
    total_students = await db.scalar(select(func.count(Student.id))) or 0
    
    # 2. Active in last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_7d = await db.scalar(
        select(func.count(Student.id)).where(Student.last_active_at >= seven_days_ago)
    ) or 0
    
    # 3. Today's activities
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    activities_today = await db.scalar(
        select(func.count(ActivityLog.id)).where(ActivityLog.created_at >= today_start)
    ) or 0
    
    percentage = (active_7d / total_students * 100) if total_students > 0 else 0
    
    # 4. Top Faculty (Most active students)
    # Group by faculty, count active students
    top_faculty_name = "N/A"
    # Simple heuristic: Faculty with most logs today
    top_fac_result = await db.execute(
        select(Faculty.name, func.count(ActivityLog.id).label('count'))
        .join(ActivityLog, ActivityLog.faculty_id == Faculty.id)
        .where(ActivityLog.created_at >= seven_days_ago)
        .group_by(Faculty.name)
        .order_by(desc('count'))
        .limit(1)
    )
    top_fac = top_fac_result.first()
    if top_fac:
        top_faculty_name = top_fac[0]

    return {
        "total_students": total_students,
        "active_students_7d": active_7d,
        "active_percentage": round(percentage, 1),
        "total_activities_today": activities_today,
        "top_faculty": top_faculty_name
    }

@router.get("/trend", response_model=List[ActivityTrendItem])
async def get_activity_trend(
    days: int = Query(30),
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity count trend for last N days.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # SQLite logic (strftime) - adjust if switching to Postgres
    # Assuming SQLite for now based on project context, but providing standardized date func
    date_func = func.date(ActivityLog.created_at) 
    
    results = await db.execute(
        select(date_func.label("day"), func.count(ActivityLog.id))
        .where(ActivityLog.created_at >= start_date)
        .group_by("day")
        .order_by("day")
    )
    
    data = []
    rows = results.all()
    # Fill missing days logic on frontend or here
    for r in rows:
        data.append({"date": str(r[0]), "count": r[1]})
        
    return data

@router.get("/faculties", response_model=List[FacultyActivityItem])
async def get_faculty_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed activity stats per faculty.
    """
    # 1. Get Faculties
    faculties = (await db.execute(select(Faculty))).scalars().all()
    
    stats = []
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    for f in faculties:
        # Optimizable: Single complex query instead of N+1 loop
        # For prototype, loop is fine
        student_count = await db.scalar(
            select(func.count(Student.id)).where(Student.faculty_id == f.id)
        ) or 0
        
        activity_count = await db.scalar(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.faculty_id == f.id,
                ActivityLog.created_at >= seven_days_ago
            )
        ) or 0
        
        avg = activity_count / student_count if student_count > 0 else 0
        
        stats.append({
            "id": f.id,
            "name": f.name,
            "activity_count": activity_count,
            "student_count": student_count,
            "avg_activity": round(avg, 2)
        })
        
    # Sort by activity count desc
    stats.sort(key=lambda x: x['activity_count'], reverse=True)
    return stats

@router.get("/students", response_model=dict)
async def search_students_by_activity(
    query: Optional[str] = None,
    faculty_id: Optional[int] = None,
    activity_level: Optional[str] = Query(None, description="High, Medium, Low, Inactive"),
    sort_by: str = Query("activity", description="activity, login, name"),
    page: int = 1,
    limit: int = 20,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Search and filter students based on activity metrics.
    """
    stmt = select(Student)
    
    # 1. Text Search
    if query:
        stmt = stmt.where(or_(
            Student.full_name.ilike(f"%{query}%"),
            Student.hemis_id.ilike(f"%{query}%")
        ))
        
    # 2. Faculty
    if faculty_id:
        stmt = stmt.where(Student.faculty_id == faculty_id)
        
    # 3. Activity Level Logic (Heuristic based on total_activity_count)
    # Define thresholds: High > 50, Medium > 10, Low > 0, Inactive = 0
    # Note: Using total_activity_count is lifetime. For periodic, we need aggregation table.
    # Using lifetime for simplicity as per requirement "Faollik darajasi"
    
    if activity_level == "High":
        stmt = stmt.where(Student.total_activity_count >= 50)
    elif activity_level == "Medium":
        stmt = stmt.where(and_(Student.total_activity_count >= 10, Student.total_activity_count < 50))
    elif activity_level == "Low":
        stmt = stmt.where(and_(Student.total_activity_count > 0, Student.total_activity_count < 10))
    elif activity_level == "Inactive":
        stmt = stmt.where(Student.total_activity_count == 0)
        
    # 4. Sorting
    if sort_by == "activity":
        stmt = stmt.order_by(desc(Student.total_activity_count))
    elif sort_by == "login":
        stmt = stmt.order_by(desc(Student.last_active_at))
    else:
        stmt = stmt.order_by(Student.full_name)
        
    # Pagination
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(stmt)
    students = result.scalars().all()
    
    data = []
    for s in students:
        # Determine status string
        status = "Inactive"
        if s.total_activity_count >= 50: status = "High"
        elif s.total_activity_count >= 10: status = "Medium"
        elif s.total_activity_count > 0: status = "Low"
        
        data.append({
            "id": s.id,
            "full_name": s.full_name,
            "faculty_name": s.faculty_name,
            "image_url": s.image_url,
            "total_activity_count": s.total_activity_count,
            "last_active_at": s.last_active_at,
            "status": status
        })
        
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit
    }

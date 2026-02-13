from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

from database.db_connect import get_db
from database.models import Student, Staff, UserActivity, Faculty, StaffRole
from api.dependencies import get_current_staff

router = APIRouter()

# ============================================================
# DASHBOARD SCHEMAS
# ============================================================
from pydantic import BaseModel

class DashboardStatsData(BaseModel):
    total_activities: int
    pending_count: int
    approved_count: int
    rejected_count: int
    activities_this_month: int
    category_breakdown: Dict[str, int]

class DashboardStatsResponse(BaseModel):
    success: bool
    data: DashboardStatsData
    
class RecentSubmissionItem(BaseModel):
    id: int
    student_name: str
    faculty_name: Optional[str]
    category: str
    name: str
    description: Optional[str] = None
    date: str
    status: str
    created_at: datetime
    images: List[str] = []

# ============================================================
# ENDPOINTS
# ============================================================

# Role Definitions
DEAN_LEVEL_ROLES = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT, StaffRole.YOSHLAR_YETAKCHISI, StaffRole.YOSHLAR_ITTIFOQI]
GLOBAL_MGMT_ROLES = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]

@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get KPI stats for Social Activities (UserActivity).
    """
    staff_role = getattr(staff, "role", None)
    logger.info(f"Social Stats Request: staff_id={staff.id}, role={staff_role}")
    
    if staff_role not in GLOBAL_MGMT_ROLES and staff_role not in DEAN_LEVEL_ROLES and staff_role != StaffRole.TYUTOR:
        logger.warning(f"Access Denied: staff_role={staff_role} not in allowed roles")
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    # Base query for filtering
    uni_id = getattr(staff, "university_id", None)
    f_id = getattr(staff, "faculty_id", None)
    
    # Base stmt for scoping
    def apply_scoping(stmt_obj):
        logger.debug(f"Applying Scoping: role={staff_role}, uni_id={uni_id}, f_id={f_id}")
        
        # 1. University Check
        if uni_id:
            stmt_obj = stmt_obj.where(Student.university_id == uni_id)
        elif staff_role not in GLOBAL_MGMT_ROLES:
            logger.error(f"Scoping Error: staff_id={staff.id} has no university_id")
            return None 

        # 2. Faculty Scoping
        # Global roles see everything if no faculty_id is assigned
        is_global = staff_role in GLOBAL_MGMT_ROLES and f_id is None
        
        if is_global:
            logger.debug(f"Global Access Granted for role={staff_role}")
            return stmt_obj
            
        if f_id:
            logger.debug(f"Faculty Scoping: f_id={f_id}")
            stmt_obj = stmt_obj.where(Student.faculty_id == f_id)
        elif staff_role in DEAN_LEVEL_ROLES or staff_role == StaffRole.TYUTOR:
            logger.warning(f"Restricted Role with no Faculty: staff_id={staff.id}")
            return None # Force zero results
            
        return stmt_obj

    # 1. Total Activity Count
    base_count_stmt = select(func.count(UserActivity.id)).join(Student, UserActivity.student_id == Student.id)
    base_count_stmt = apply_scoping(base_count_stmt)
    if base_count_stmt is None:
        return {"success": True, "data": DashboardStatsData(total_activities=0, pending_count=0, approved_count=0, rejected_count=0, activities_this_month=0, category_breakdown={})}
    
    total_activities = await db.scalar(base_count_stmt) or 0
    
    # 2. Status Counts (Scoped)
    status_stmt = select(UserActivity.status, func.count(UserActivity.id)).join(Student, UserActivity.student_id == Student.id)
    status_stmt = apply_scoping(status_stmt)
    status_counts_res = await db.execute(status_stmt.group_by(UserActivity.status))
    status_map = {r[0]: r[1] for r in status_counts_res.all()}
    
    pending_count = status_map.get("pending", 0)
    approved_count = status_map.get("confirmed", 0) 
    rejected_count = status_map.get("rejected", 0)

    # 3. Activities this month (Scoped)
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_stmt = select(func.count(UserActivity.id)).join(Student, UserActivity.student_id == Student.id).where(UserActivity.created_at >= start_of_month)
    month_stmt = apply_scoping(month_stmt)
    activities_this_month = await db.scalar(month_stmt) or 0
    
    # 4. Category Breakdown (Scoped)
    cat_stmt = select(UserActivity.category, func.count(UserActivity.id)).join(Student, UserActivity.student_id == Student.id)
    cat_stmt = apply_scoping(cat_stmt)
    cat_counts_res = await db.execute(cat_stmt.group_by(UserActivity.category))
    category_breakdown = {str(r[0] or "boshqa"): r[1] for r in cat_counts_res.all()}

    return {
        "success": True,
        "data": {
            "total_activities": total_activities,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "activities_this_month": activities_this_month,
            "category_breakdown": category_breakdown
        }
    }

@router.get("/recent-submissions", response_model=List[RecentSubmissionItem])
async def get_recent_submissions(
    limit: int = 10,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    staff_role = str(getattr(staff, "role", None)).lower()
    if staff_role not in GLOBAL_MGMT_ROLES and staff_role not in DEAN_LEVEL_ROLES and staff_role != 'tyutor':
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    uni_id = getattr(staff, "university_id", None)
    f_id = getattr(staff, "faculty_id", None)

    stmt = (
        select(UserActivity)
        .join(Student, UserActivity.student_id == Student.id)
        .options(
            selectinload(UserActivity.student),
            selectinload(UserActivity.images)
        )
        .order_by(desc(UserActivity.created_at))
        .limit(limit)
    )

    if uni_id:
        stmt = stmt.where(Student.university_id == uni_id)
    
    # Scoping logic mirror
    is_global = staff_role in GLOBAL_MGMT_ROLES and f_id is None
    if not is_global:
        if f_id:
            stmt = stmt.where(Student.faculty_id == f_id)
        elif staff_role in DEAN_LEVEL_ROLES or staff_role == StaffRole.TYUTOR:
            return [] # Restricted but no faculty assigned
    
    results = await db.scalars(stmt)
    items = []
    
    for act in results.all():
        student_name = "Unknown"
        faculty_name = None
        if act.student:
            student_name = act.student.full_name
            faculty_name = act.student.faculty_name
            
        activity_images = []
        if act.images:
            # Construct full URLs for static images
            # Assuming file_id is a relative path like 'static/uploads/...' or similar
            # Or just use file_id if it's already a full URL/suitable for frontend
            for img in act.images:
                url = img.file_id
                if url and not url.startswith(('http', '/')):
                    url = f"https://tengdosh.uzjoku.uz/{url}" 
                elif url and url.startswith('static/'):
                    url = f"https://tengdosh.uzjoku.uz/{url}"
                activity_images.append(url)

        items.append({
            "id": act.id,
            "student_name": student_name,
            "faculty_name": faculty_name,
            "category": act.category,
            "name": act.name,
            "description": act.description,
            "date": act.date or "",
            "status": act.status,
            "created_at": act.created_at,
            "images": activity_images
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
    staff_role = getattr(staff, "role", None)
    f_id = getattr(staff, "faculty_id", None)
    is_global = staff_role in GLOBAL_MGMT_ROLES and f_id is None
    
    # 1. Get Faculties
    stmt = select(Faculty)
    if not is_global:
        if f_id:
            stmt = stmt.where(Faculty.id == f_id)
        else:
            return [] # Restricted but no faculty assigned (Safety Block)
    
    faculties = (await db.execute(stmt)).scalars().all()
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

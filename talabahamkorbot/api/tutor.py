from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from database.db_connect import get_session
from database.models import Staff, TutorGroup, Student, StaffRole, TyutorKPI
from api.dependencies import get_current_staff

router = APIRouter(prefix="/tutor", tags=["Tutor"])

@router.get("/groups")
async def get_tutor_groups(
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get list of groups assigned to this tutor.
    """
    groups = await db.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor.id))
    return {
        "success": True, 
        "data": [
            {"id": g.id, "group_number": g.group_number, "faculty_id": g.faculty_id} 
            for g in groups.scalars().all()
        ]
    }

@router.get("/dashboard")
async def get_tutor_dashboard(
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get dashboard stats (Total students, KPI, etc.)
    """
    # 1. Get Groups
    groups_result = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor.id))
    group_numbers = groups_result.scalars().all()
    
    if not group_numbers:
        return {"success": True, "data": {"student_count": 0, "group_count": 0, "kpi": 0}}
        
    # 2. Count Students
    student_count = await db.scalar(
        select(func.count(Student.id)).where(Student.group_number.in_(group_numbers))
    )
    
    # 3. KPI
    from datetime import datetime
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    
    kpi_obj = await db.scalar(
        select(TyutorKPI)
        .where(
            TyutorKPI.tyutor_id == tutor.id,
            TyutorKPI.quarter == quarter,
            TyutorKPI.year == year
        )
    )
    
    kpi = kpi_obj.total_kpi if kpi_obj else 0.0
    
    return {
        "success": True,
        "data": {
            "student_count": student_count,
            "group_count": len(group_numbers),
            "kpi": kpi,
            "groups": group_numbers
        }
    }

@router.get("/students")
async def get_tutor_students(
    group: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get students. Optionally filter by group or search by name.
    Restricted to the tutor's assigned groups.
    """
    # 1. Get Tutor's Groups
    groups_result = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor.id))
    my_groups = groups_result.scalars().all()
    
    if not my_groups:
        return {"success": True, "data": []}
        
    # 2. Build Query
    stmt = select(Student).where(Student.group_number.in_(my_groups))
    
    if group and group in my_groups:
        stmt = stmt.where(Student.group_number == group)
        
    if search:
        stmt = stmt.where(Student.full_name.ilike(f"%{search}%"))
        
    stmt = stmt.limit(50)
    
    students = await db.execute(stmt)
    
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "full_name": s.full_name,
                "group": s.group_number,
                "hemis_id": s.hemis_id,
                "image": s.image_url
            }
            for s in students.scalars().all()
        ]
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from database.db_connect import get_session
from database.models import Staff, TutorGroup, Student, StaffRole, TyutorKPI, StudentFeedback, FeedbackReply
from api.dependencies import get_current_staff

router = APIRouter(prefix="/tutor", tags=["Tutor"])

@router.get("/groups")
async def get_tutor_groups(
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get list of groups assigned to this tutor with unread appeals count.
    """
    # 1. Get Groups
    groups_result = await db.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor.id))
    groups = groups_result.scalars().all()
    
    result_data = []
    
    for g in groups:
        # 2. Count unread appeals for this group
        # Student -> StudentFeedback (status='pending')
        # We need to join Student and StudentFeedback
        unread_count = await db.scalar(
            select(func.count(StudentFeedback.id))
            .join(Student, StudentFeedback.student_id == Student.id)
            .where(
                Student.group_number == g.group_number,
                StudentFeedback.status == 'pending'
            )
        )
        
        result_data.append({
            "id": g.id, 
            "group_number": g.group_number, 
            "faculty_id": g.faculty_id,
            "unread_appeals_count": unread_count or 0
        })

    return {
        "success": True, 
        "data": result_data
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

@router.get("/groups/{group_number}/appeals")
async def get_group_appeals(
    group_number: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get appeals from students in a specific group assigned to the tutor.
    """
    # 1. Verify Tutor Access to Group
    # Theoretically 'get_tutor_groups' logic, but direct check is faster
    has_access = await db.scalar(
        select(TutorGroup)
        .where(
            TutorGroup.tutor_id == tutor.id,
            TutorGroup.group_number == group_number
        )
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access to this group denied")

    # 2. Query Appeals
    stmt = (
        select(StudentFeedback, Student)
        .join(Student, StudentFeedback.student_id == Student.id)
        .where(Student.group_number == group_number)
        .order_by(StudentFeedback.created_at.desc())
    )

    if status:
        stmt = stmt.where(StudentFeedback.status == status)

    result = await db.execute(stmt)
    rows = result.all() # list of (StudentFeedback, Student)
    
    data = []
    for feedback, student in rows:
        data.append({
            "id": feedback.id,
            "student_id": student.id,
            "student_name": student.full_name,
            "student_image": student.image_url,
            "student_faculty": student.faculty_name or "", 
            "student_group": student.group_number or "",
            "text": feedback.text,
            "status": feedback.status,
            "created_at": feedback.created_at.isoformat(),
            "file_id": feedback.file_id,
            "file_type": feedback.file_type
        })

    return {
        "success": True,
        "data": data
    }

@router.post("/appeals/{appeal_id}/reply")
async def reply_to_appeal(
    appeal_id: int,
    text: str,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Reply to a student appeal.
    """
    # 1. Get Appeal and Verify Access
    result = await db.execute(
        select(StudentFeedback, Student)
        .join(Student, StudentFeedback.student_id == Student.id)
        .where(StudentFeedback.id == appeal_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Appeal not found")
        
    feedback, student = row
    
    # 2. Check if student is in one of tutor's groups
    has_access = await db.scalar(
        select(TutorGroup)
        .where(
            TutorGroup.tutor_id == tutor.id,
            TutorGroup.group_number == student.group_number
        )
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="You do not have access to this student's appeals")

    # 3. Create Reply
    reply = FeedbackReply(
        feedback_id=feedback.id,
        staff_id=tutor.id,
        text=text
    )
    db.add(reply)
    
    # 4. Update Status
    feedback.status = "answered"
    feedback.assigned_staff_id = tutor.id
    
    await db.commit()
    
    return {"success": True, "message": "Reply sent successfully"}

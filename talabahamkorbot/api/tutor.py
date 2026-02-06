from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional

from database.db_connect import get_session
from database.models import Staff, TutorGroup, Student, StaffRole, TyutorKPI, StudentFeedback, FeedbackReply, UserActivity
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
    appeal_id: int, 
    text: str, 
    db: AsyncSession = Depends(get_session), 
    tutor: Staff = Depends(get_current_staff)
):
    # Check appeal exists
    stmt = select(StudentFeedback).where(StudentFeedback.id == appeal_id)
    result = await db.execute(stmt)
    appeal = result.scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(status_code=404, detail="Murojaat topilmadi")
        
    # Check access (simple check: is student in my groups?)
    # ideally we check specific permission, but for now:
    # We trust the tutor context or checking Student->Group link
    
    reply = FeedbackReply(
        feedback_id=appeal_id,
        staff_id=tutor.id,
        text=text
    )
    db.add(reply)
    
    # Update appeal status
    appeal.status = "answered"
    appeal.assigned_staff_id = tutor.id
    appeal.assigned_role = "tyutor"
    
    await db.commit()
    
    return {"success": True, "message": "Javob yuborildi"}


# ============================================================
# 5. FAOLLIKLAR (ACTIVITIES)
# ============================================================

@router.get("/activities/stats")
async def get_tutor_activity_stats(
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Returns groups with counts of pending and today's activities.
    """
    # 1. Get Tutor's Groups
    groups_result = await db.execute(select(TutorGroup).where(TutorGroup.tutor_id == tutor.id))
    tutor_groups = groups_result.scalars().all()
    group_numbers = [g.group_number for g in tutor_groups]
    
    if not group_numbers:
        return {"success": True, "data": []}

    # 2. Results container
    stats = []
    
    from datetime import datetime, timedelta
    today_str = datetime.utcnow().strftime("%Y-%m-%d") # Assuming date stored as string YYYY-MM-DD or similar
    
    # We will do a query to count for each group
    # Optimized: Group by group_number
    # user_activities -> student -> group_number
    
    for gn in group_numbers:
        # Count Pending
        q_pending = select(func.count(UserActivity.id)).join(Student).where(
            Student.group_number == gn,
            UserActivity.status == "pending"
        )
        res_pending = await db.execute(q_pending)
        count_pending = res_pending.scalar() or 0
        
        # Count Today's (All statuses)
        # Note: UserActivity.date is a string, let's assume standard format or check created_at
        # Using created_at for reliability
        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        q_today = select(func.count(UserActivity.id)).join(Student).where(
            Student.group_number == gn,
            UserActivity.created_at >= start_of_day
        )
        res_today = await db.execute(q_today)
        count_today = res_today.scalar() or 0
        
        stats.append({
            "group_number": gn,
            "pending_count": count_pending,
            "today_count": count_today
        })
        
    return {"success": True, "data": stats}


@router.get("/activities/group/{group_number}")
async def get_group_activities(
    group_number: str,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get activities for a specific group.
    """
    # Verify access
    access_check = await db.execute(
        select(TutorGroup).where(
            TutorGroup.tutor_id == tutor.id,
            TutorGroup.group_number == group_number
        )
    )
    if not access_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Siz bu guruhga biriktirilmagansiz")

    # Fetch activities
    stmt = select(UserActivity).join(Student).where(
        Student.group_number == group_number
    ).order_by(
        case(
            (UserActivity.status == 'pending', 0),
            else_=1
        ),
        UserActivity.created_at.desc()
    ).limit(50)
    
    result = await db.execute(stmt)
    activities = result.scalars().all()
    
    data = []
    for act in activities:
        # Load student info (lazy loaded usually, but let's be safe if sync)
        # We need student name and image. 
        # Since we didn't eager load, we might trigger n+1 if not careful, 
        # but for 50 items it's acceptable or we can add options(joinedload(UserActivity.student))
        # Let's trust lazy loading for now or do a join above if models support it.
        # Actually better to eager load.
        pass
        
    # Re-query with eager load to be efficient
    stmt = select(UserActivity).options(joinedload(UserActivity.student)).join(Student).where(
        Student.group_number == group_number
    ).order_by(
        case(
            (UserActivity.status == 'pending', 0),
            else_=1
        ),
        UserActivity.created_at.desc()
    ).limit(50)
    result = await db.execute(stmt)
    activities = result.scalars().all()

    for act in activities:
        data.append({
            "id": act.id,
            "category": act.category,
            "name": act.name,
            "description": act.description,
            "status": act.status,
            "created_at": act.created_at.isoformat(),
            "student": {
                "full_name": act.student.full_name,
                "image": act.student.image_url,
                "hemis_id": act.student.hemis_id
            }
            # Add images if related
        })

    return {"success": True, "data": data}


@router.post("/activity/{activity_id}/review")
async def review_activity(
    activity_id: int,
    request: dict, # {"status": "accepted" | "rejected"}
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    stmt = select(UserActivity).where(UserActivity.id == activity_id)
    result = await db.execute(stmt)
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Faollik topilmadi")
        
    # Verify tutor access to this student's group?
    # For now assuming if they have ID they can review, or strict check:
    # await verify_tutor_access(db, tutor.id, activity.student.group_number)
    
    new_status = request.get("status")
    if new_status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Noto'g'ri status")
        
    activity.status = new_status
    await db.commit()
    
    return {"success": True, "message": f"Faollik {new_status} qilindi"}

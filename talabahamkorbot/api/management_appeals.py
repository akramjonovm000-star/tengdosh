from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database.db_connect import get_db
from database.models import Student, StudentFeedback, Faculty, Staff, FeedbackReply, StaffRole
from api.dependencies import get_current_staff, get_db
from pydantic import BaseModel

router = APIRouter(prefix="/management/appeals", tags=["Management Appeals"])

from api.schemas_appeals import AppealStats as AppealStatsModel, AppealItem

@router.get("/stats", response_model=AppealStatsModel)
async def get_appeals_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Auth Check
        dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
        global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
        
        current_role = getattr(staff, 'role', None) or ""
        is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or current_role in global_mgmt_roles or current_role in dean_level_roles
        
        if not is_mgmt:
            raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki dekanat uchun")
            
        uni_id = getattr(staff, 'university_id', None)
        if not uni_id:
            # Fallback if university_id missing (superuser?)
            return {"total": 0, "counts": {}, "faculty_performance": [], "top_targets": []}
        
        # 2. Overall Counts
        stmt = select(StudentFeedback.status, func.count(StudentFeedback.id)).join(Student)\
            .where(Student.university_id == uni_id)
            
        f_id = getattr(staff, 'faculty_id', None)
        if current_role in dean_level_roles and f_id:
            stmt = stmt.where(Student.faculty_id == f_id)
            # [NEW] Enforce Bakalavr Only
            stmt = stmt.where(Student.education_type.ilike("Bakalavr"))
            
        stmt = stmt.group_by(StudentFeedback.status)
        rows = (await db.execute(stmt)).all()
        
        counts = {"pending": 0, "processing": 0, "resolved": 0, "replied": 0}
        total = 0
        for status, count in rows:
            # Normalized status check if needed
            s = status.lower() if status else "pending"
            counts[s] = count
            total += count
            
        # 3. Faculty Performance
        # Using existing snapshot 'student_faculty' in StudentFeedback
        fac_stmt = select(StudentFeedback.student_faculty, StudentFeedback.status, func.count(StudentFeedback.id))\
            .join(Student).where(Student.university_id == uni_id)\
            .group_by(StudentFeedback.student_faculty, StudentFeedback.status)
            
        fac_rows = (await db.execute(fac_stmt)).all()
        
        fac_stats = {}
        for fac, status, count in fac_rows:
            if not fac: fac = "Boshqa"
            
            if fac not in fac_stats: 
                fac_stats[fac] = {"total": 0, "resolved": 0, "pending": 0}
                
            fac_stats[fac]["total"] += count
            
            if status in ['resolved', 'replied']:
                 fac_stats[fac]["resolved"] += count
            else:
                 fac_stats[fac]["pending"] += count
                 
        faculty_performance = []
        for fac, data in fac_stats.items():
            rate = (data["resolved"] / data["total"]) * 100 if data["total"] > 0 else 0
            faculty_performance.append({
                "faculty": fac,
                "total": data["total"],
                "resolved": data["resolved"],
                "rate": round(rate, 1)
            })
        
        # Sort by total appeals descending
        faculty_performance.sort(key=lambda x: x["total"], reverse=True)
        
        # 4. Top Targets (Who is receiving appeals?)
        role_stmt = select(StudentFeedback.assigned_role, func.count(StudentFeedback.id))\
            .join(Student).where(Student.university_id == uni_id)\
            .group_by(StudentFeedback.assigned_role)
        role_rows = (await db.execute(role_stmt)).all()
        
        top_targets = [{"role": r or "Noma'lum", "count": c} for r, c in role_rows]
        top_targets.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "total": total,
            "counts": counts,
            "faculty_performance": faculty_performance,
            "top_targets": top_targets
        }
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"APPEALS_STATS ERROR: {e}")
        logger.error(traceback.format_exc())
        return {"total": 0, "counts": {}, "faculty_performance": [], "top_targets": []}

@router.get("/list", response_model=List[AppealItem])
async def get_appeals_list(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    faculty: Optional[str] = None,
    ai_topic: Optional[str] = None,
    assigned_role: Optional[str] = None,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Auth Check
        is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
        if not is_mgmt:
            raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
        uni_id = getattr(staff, 'university_id', None)
        
        query = select(StudentFeedback).join(Student).where(Student.university_id == uni_id)
        
        # [NEW] Faculty Scoping for Deans
        f_id = getattr(staff, 'faculty_id', None)
        current_role = getattr(staff, 'role', None) 
        dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
        
        if current_role in dean_level_roles and f_id:
            query = query.where(Student.faculty_id == f_id)
            # [NEW] Enforce Bakalavr Only
            query = query.where(Student.education_type.ilike("Bakalavr"))
        elif faculty:
            # If manually filtering, apply status rules
            pass

        # Apply Status Filter
        if status:
            if status == 'active': # Custom filter for Pending+Processing
                 query = query.where(StudentFeedback.status.in_(['pending', 'processing']))
            elif status == 'resolved':
                 query = query.where(StudentFeedback.status.in_(['resolved', 'replied']))
            else:
                 query = query.where(StudentFeedback.status == status)

        # Apply Faculty Filter
        if faculty:
            if faculty == "Boshqa":
                 query = query.where(or_(StudentFeedback.student_faculty == None, StudentFeedback.student_faculty == ""))
            else:
                 query = query.where(StudentFeedback.student_faculty == faculty)
            
        if ai_topic:
            query = query.where(StudentFeedback.ai_topic == ai_topic)
    
        if assigned_role:
            query = query.where(StudentFeedback.assigned_role == assigned_role)
            
        # Order by newest
        query = query.order_by(StudentFeedback.created_at.desc())
        
        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        res = await db.execute(query)
        appeals = res.scalars().all()
        
        return [
            {
                "id": a.id,
                "text": a.text,
                "status": a.status,
                "student_name": a.student_full_name or "Noma'lum", 
                "student_faculty": a.student_faculty or "Noma'lum",
                "student_group": a.student_group,
                "student_phone": a.student_phone,
                "ai_topic": a.ai_topic,
                "created_at": a.created_at.isoformat(),
                "assigned_role": a.assigned_role or "Umumiy",
                "is_anonymous": a.is_anonymous
            } for a in appeals
        ]
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"APPEALS_LIST ERROR: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Murojaatlarni yuklab bo'lmadi")

@router.get("/{id}")
async def get_appeal_detail(
    id: int,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed appeal thread for management.
    """
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    stmt = (
        select(StudentFeedback)
        .join(Student)
        .where(StudentFeedback.id == id)
        .where(Student.university_id == uni_id)
        .options(
            selectinload(StudentFeedback.replies), 
            selectinload(StudentFeedback.children),
            selectinload(StudentFeedback.student)
        )
    )
    
    # [NEW] Faculty Scoping for Deans
    f_id = getattr(staff, 'faculty_id', None)
    current_role = getattr(staff, 'role', None)
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    
    if current_role in dean_level_roles and f_id:
        stmt = stmt.where(Student.faculty_id == f_id)
        # [NEW] Enforce Bakalavr Only
        stmt = stmt.where(Student.education_type.ilike("Bakalavr"))
        
    appeal = await db.scalar(stmt)
    
    if not appeal:
        raise HTTPException(status_code=404, detail="Murojaat topilmadi")
        
    messages = []
    
    # 1. Root Message
    messages.append({
        "id": appeal.id,
        "sender": "me",
        "text": appeal.text,
        "time": appeal.created_at.strftime("%H:%M") if appeal.created_at else "--:--",
        "timestamp": appeal.created_at or datetime.utcnow(),
        "file_id": appeal.file_id
    })
    
    # 2. Staff Replies
    for reply in (appeal.replies or []):
        messages.append({
            "id": reply.id,
            "sender": "staff",
            "text": reply.text or "[Fayl]",
            "time": reply.created_at.strftime("%H:%M") if reply.created_at else "--:--",
            "timestamp": reply.created_at or datetime.utcnow(),
            "file_id": reply.file_id
        })
        
    # 3. Student Follow-ups
    for child in (appeal.children or []):
        messages.append({
            "id": child.id,
            "sender": "me",
            "text": child.text,
            "time": child.created_at.strftime("%H:%M") if child.created_at else "--:--",
            "timestamp": child.created_at or datetime.utcnow(),
            "file_id": child.file_id
        })

    messages.sort(key=lambda x: x['timestamp'])

    return {
        "id": appeal.id,
        "title": f"Murojaat #{appeal.id}",
        "status": appeal.status,
        "date": appeal.created_at.strftime("%d.%m.%Y"),
        "student": {
            "name": appeal.student_full_name or (appeal.student.full_name if appeal.student else "Noma'lum"),
            "faculty": appeal.student_faculty,
            "group": appeal.student_group,
            "phone": appeal.student_phone,
            "is_anonymous": appeal.is_anonymous
        },
        "messages": messages
    }

@router.post("/{id}/resolve")
async def resolve_appeal(
    id: int,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    stmt = select(StudentFeedback).where(StudentFeedback.id == id)
    appeal = (await db.execute(stmt)).scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(404, "Murojaat topilmadi")
        
    appeal.status = 'resolved'
    appeal.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(appeal) # Refresh the appeal object after commit

    # [NEW] Log Activity
    from services.activity_service import ActivityService, ActivityType
    await ActivityService.log_activity(
        db=db,
        user_id=staff.id, # Assuming 'staff' is the user resolving the appeal
        role='management', # Or appropriate role for staff
        activity_type=ActivityType.APPEAL_RESOLUTION, # A new activity type for resolution
        ref_id=appeal.id
    )
    
    return {"success": True, "message": "Murojaat yopildi"}

@router.post("/{id}/reply")
async def reply_to_appeal(
    id: int,
    text: str = Body(..., embed=True),
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Management reply to an appeal.
    Sets status to 'answered'.
    """
    # 1. Auth Check
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in ['rahbariyat', 'admin', 'owner']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    # 2. Fetch Appeal
    stmt = select(StudentFeedback).where(StudentFeedback.id == id)
    appeal = (await db.execute(stmt)).scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(status_code=404, detail="Murojaat topilmadi")

    # 3. Create Reply
    reply = FeedbackReply(
        feedback_id=id,
        staff_id=staff.id,
        text=text
    )
    db.add(reply)

    # 4. Update Status
    appeal.status = 'answered'
    appeal.assigned_staff_id = staff.id
    appeal.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "message": "Javob yuborildi"}

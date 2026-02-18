from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import selectinload
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
        # 1. Auth Check & Scoping
        dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
        global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
        
        current_role = getattr(staff, 'role', None) or ""
        f_id = getattr(staff, 'faculty_id', None)
        is_global = current_role in global_mgmt_roles and f_id is None
        is_mgmt = current_role in global_mgmt_roles or current_role in dean_level_roles
        
        if not is_mgmt:
            raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki dekanat uchun")
            
        uni_id = getattr(staff, 'university_id', None)
        if not uni_id:
            # Fallback if university_id missing (superuser?)
            return {
                "total": 0, 
                "counts": {}, 
                "total_active": 0,
                "total_resolved": 0,
                "faculty_performance": [], 
                "top_targets": []
            }
        
        # 2. Overall Counts & Overdue
        now = datetime.utcnow()
        three_days_ago = now - timedelta(days=3)
        
        # Base Query
        base_query = select(StudentFeedback).join(Student).where(Student.university_id == uni_id)
        
        if not is_global and f_id:
            base_query = base_query.where(Student.faculty_id == f_id)
            
        all_appeals = (await db.execute(base_query)).scalars().all()
        
        counts = {"pending": 0, "processing": 0, "resolved": 0, "replied": 0}
        total_overdue = 0
        
        # In-memory aggregation for flexibility (or complex SQL for performance if dataset > 10k)
        # Given dataset size likely < 10k active, in-memory is fine and cleaner for logic
        
        # Pivot Stats: Faculty list for Global, Group list for Deans
        pivot_stats = {} 
        
        for a in all_appeals:
            status = a.status or "pending"
            counts[status] = counts.get(status, 0) + 1
            
            # Pivot logic: Group by Faculty if global, by Group if scoped
            if is_global:
                pivot_name = a.student_faculty or "Boshqa"
            else:
                pivot_name = a.student_group or "Noma'lum"
            
            if pivot_name not in pivot_stats:
                pivot_stats[pivot_name] = {
                    "total": 0, "resolved": 0, "pending": 0, "overdue": 0, 
                    "response_times": [], "topics": {}
                }
            
            ps = pivot_stats[pivot_name]
            ps["total"] += 1
            
            # Topic Breakdown
            topic = a.ai_topic or "Boshqa"
            ps["topics"][topic] = ps["topics"].get(topic, 0) + 1
            
            # Status Stats
            if status in ['resolved', 'replied']:
                ps["resolved"] += 1
                # Response Time Calc
                if a.created_at and a.updated_at and a.updated_at > a.created_at:
                    diff = (a.updated_at - a.created_at).total_seconds() / 3600 # Hours
                    if diff > 0 and diff < 10000: # Sanity check
                        ps["response_times"].append(diff)
            else:
                ps["pending"] += 1
                # Overdue Calc
                if a.created_at and a.created_at < three_days_ago:
                    ps["overdue"] += 1
                    total_overdue += 1

        # 3. Build Performance List (Faculties or Groups)
        performance_list = []
        
        # Helper to get Faculty IDs (only if global)
        name_to_id = {}
        if is_global:
            fac_map_stmt = select(Faculty.id, Faculty.name).where(Faculty.university_id == uni_id)
            fac_map_rows = (await db.execute(fac_map_stmt)).all()
            name_to_id = {r[1]: r[0] for r in fac_map_rows}
        
        for p_name, data in pivot_stats.items():
            avg_time = 0.0
            if data["response_times"]:
                avg_time = sum(data["response_times"]) / len(data["response_times"])
                
            rate = (data["resolved"] / data["total"]) * 100 if data["total"] > 0 else 0
            
            performance_list.append({
                "faculty": p_name, # Generic field name used by frontend
                "id": name_to_id.get(p_name),
                "total": data["total"],
                "resolved": data["resolved"],
                "pending": data["pending"],
                "overdue": data["overdue"],
                "avg_response_time": round(avg_time, 1),
                "rate": round(rate, 1),
                "topics": data["topics"]
            })
            
        # Sort by Overdue (Priority) then Total
        performance_list.sort(key=lambda x: (x["overdue"], x["total"]), reverse=True)
        
        # 4. Top Targets
        # Reuse loop data or simple count
        top_targets_map = {}
        for a in all_appeals:
            role = a.assigned_role or "Noma'lum"
            top_targets_map[role] = top_targets_map.get(role, 0) + 1
            
        top_targets = [{"role": r, "count": c} for r, c in top_targets_map.items()]
        top_targets.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "total": counts["pending"] + counts["processing"] + counts["resolved"] + counts["replied"],
            "counts": counts,
            "total_active": counts["pending"] + counts["processing"],
            "total_resolved": counts["resolved"] + counts["replied"],
            "total_overdue": total_overdue, 
            "breakdown_title": "Guruhlar Kesimida" if not is_global else "Fakultetlar Kesimida",
            "faculty_performance": performance_list, # Reuse key for both breakdown types
            "top_targets": top_targets
        }
    except Exception as e:
        import traceback
        import logging
        
        # Write to file
        with open("debug_error.log", "w") as f:
            f.write(f"ERROR: {str(e)}\n")
            f.write(traceback.format_exc())
            
        logger = logging.getLogger(__name__)
        logger.error(f"APPEALS_STATS ERROR: {e}")
        logger.error(traceback.format_exc())
        
        # DEBUG: Return traceback to user to identify the issue
        tb_str = traceback.format_exc()[-300:] # Last 300 chars
        raise HTTPException(status_code=500, detail=f"DEBUG ERROR: {str(e)} | {tb_str}")

@router.get("/list", response_model=List[AppealItem])
async def get_appeals_list(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    faculty: Optional[str] = None,
    faculty_id: Optional[int] = None, # [NEW] Filter by ID
    ai_topic: Optional[str] = None,
    assigned_role: Optional[str] = None,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Auth Check & Scoping
        dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
        global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
        
        current_role = getattr(staff, 'role', None) or ""
        f_id = getattr(staff, 'faculty_id', None)
        is_global = current_role in global_mgmt_roles and f_id is None
        is_mgmt = current_role in global_mgmt_roles or current_role in dean_level_roles
        
        if not is_mgmt:
            raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki dekanat uchun")
        
        uni_id = getattr(staff, 'university_id', None)
        
        query = select(StudentFeedback).join(Student).where(Student.university_id == uni_id)
        
        # [NEW] Mandatory Faculty Scoping for Deans/Scoped Mgmt
        if not is_global and f_id:
            query = query.where(Student.faculty_id == f_id)
            # Override any manual faculty filter from frontend if scoped
            faculty = None
            faculty_id = None
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
        if faculty_id:
            # [NEW] Filter by ID (More robust)
            query = query.where(Student.faculty_id == faculty_id)
        elif faculty:
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
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    
    current_role = getattr(staff, 'role', None) or ""
    f_id = getattr(staff, 'faculty_id', None)
    uni_id = getattr(staff, 'university_id', None)
    is_global = current_role in global_mgmt_roles and f_id is None
    is_mgmt = current_role in global_mgmt_roles or current_role in dean_level_roles
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki dekanat uchun")

    stmt = (
        select(StudentFeedback)
        .join(Student)
        .where(StudentFeedback.id == id)
        .options(
            selectinload(StudentFeedback.replies), 
            selectinload(StudentFeedback.children),
            selectinload(StudentFeedback.student)
        )
    )
    
    if uni_id:
        stmt = stmt.where(Student.university_id == uni_id)
        
    if not is_global and f_id:
        stmt = stmt.where(Student.faculty_id == f_id)
        
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
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    
    current_role = getattr(staff, 'role', None) or ""
    f_id = getattr(staff, 'faculty_id', None)
    uni_id = getattr(staff, 'university_id', None)
    is_global = current_role in global_mgmt_roles and f_id is None
    is_mgmt = current_role in global_mgmt_roles or current_role in dean_level_roles
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki dekanat uchun")

    stmt = select(StudentFeedback).join(Student).where(StudentFeedback.id == id)
    if uni_id:
        stmt = stmt.where(Student.university_id == uni_id)
    if not is_global and f_id:
        stmt = stmt.where(Student.faculty_id == f_id)
        
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
    # 1. Auth Check & Scoping
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    
    current_role = getattr(staff, 'role', None) or ""
    f_id = getattr(staff, 'faculty_id', None)
    uni_id = getattr(staff, 'university_id', None)
    is_global = current_role in global_mgmt_roles and f_id is None
    is_mgmt = current_role in global_mgmt_roles or current_role in dean_level_roles
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki dekanat uchun")

    # 2. Fetch Appeal (with scoping)
    stmt = select(StudentFeedback).join(Student).where(StudentFeedback.id == id)
    if uni_id:
        stmt = stmt.where(Student.university_id == uni_id)
    if not is_global and f_id:
        stmt = stmt.where(Student.faculty_id == f_id)
        
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

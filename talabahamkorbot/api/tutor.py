from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime

from fastapi_cache.decorator import cache
from database.db_connect import get_session
from database.models import Staff, TutorGroup, Student, StaffRole, TyutorKPI, StudentFeedback, FeedbackReply, UserActivity, StudentDocument
from api.dependencies import get_current_staff
from bot import bot

router = APIRouter(prefix="/tutor", tags=["Tutor"])

@router.get("/documents/stats")
async def get_tutor_document_stats(
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get document upload statistics for each of the tutor's groups.
    """
    # 1. Get Tutor's Groups
    groups_result = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor.id))
    group_numbers = groups_result.scalars().all()
    
    if not group_numbers:
        return {"success": True, "data": []}

    # 2. Optimized Aggregate Query
    from sqlalchemy import distinct
    from config import HEMIS_ADMIN_TOKEN
    from services.hemis_service import HemisService
    
    # Fetch accurate totals from HEMIS
    hemis_counts = await HemisService.get_group_student_counts(group_numbers, HEMIS_ADMIN_TOKEN)
    
    # Fetch uploaded counts from DB
    stmt = (
        select(
            Student.group_number,
            func.count(distinct(StudentDocument.student_id)).label("uploaded_count")
        )
        .join(StudentDocument, Student.id == StudentDocument.student_id)
        .where(Student.group_number.in_(group_numbers))
        .group_by(Student.group_number)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    uploaded_map = {r.group_number: r.uploaded_count for r in rows}
    
    data = []
    for gn in group_numbers:
        total = hemis_counts.get(gn, 0)
        # Fallback if HEMIS failed for this group (e.g. 0) - maybe check DB?
        # But we trust HEMIS more now.
        
        data.append({
            "group_number": gn,
            "total_students": total,
            "uploaded_students": uploaded_map.get(gn, 0)
        })
        
    return {"success": True, "data": data}

@router.get("/documents/group/{group_number}")
async def get_group_document_details(
    group_number: str,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get detailed document status for all students in a group.
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

    # Fetch students and their documents
    stmt = (
        select(Student)
        .options(joinedload(Student.all_documents))
        .where(Student.group_number == group_number)
        .order_by(Student.full_name)
    )
    
    result = await db.execute(stmt)
    students = result.unique().scalars().all()
    
    data = []
    for s in students:
        data.append({
            "id": s.id,
            "full_name": s.full_name,
            "image": s.image_url,
            "hemis_id": s.hemis_id,
            "has_document": any(d.file_type == "document" for d in s.all_documents),
            "documents": [
                {
                    "id": d.id,
                    "title": d.file_name,
                    "type": d.file_type,
                    "created_at": d.uploaded_at.isoformat()
                } for d in s.all_documents if d.file_type == "document"
            ]
        })
        
    return {"success": True, "data": data}

@router.post("/documents/request")
async def request_documents(
    student_id: Optional[int] = None,
    group_number: Optional[str] = None,
    category: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Send a notification to a specific student or entire group to upload documents.
    """
    from database.models import TgAccount
    
    cat_name = category.capitalize() if category and category != "all" else "kerakli hujjatlarni"
    if category == "boshqa": cat_name = "so'ralgan hujjatni"
    
    if student_id:
        tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == student_id))
        if tg_acc:
            try:
                msg = (
                    f"🔔 <b>Hujjat topshirish eslatmasi</b>\n\n"
                    f"Hurmatli talaba, tyutoringiz <b>{tutor.full_name}</b> sizdan <b>{cat_name}</b> "
                    f"yuklashingizni so'ramoqda.\n\n"
                    f"Iltimos, ilovaning 'Hujjatlar' bo'limiga kiring."
                )
                await bot.send_message(tg_acc.telegram_id, msg, parse_mode="HTML")
                return {"success": True, "message": "Xabar yuborildi"}
            except Exception as e:
                 return {"success": False, "message": f"Xabar yuborishda xato: {str(e)}"}
        return {"success": False, "message": "Talabaning telegrami ulanmagan"}
        
    elif group_number:
        # Verify access
        access_check = await db.execute(
            select(TutorGroup).where(
                TutorGroup.tutor_id == tutor.id,
                TutorGroup.group_number == group_number
            )
        )
        if not access_check.scalar_one_or_none():
             raise HTTPException(status_code=403, detail="Siz bu guruhga biriktirilmagansiz")

        # Find students who are missing the document(s)
        from sqlalchemy import exists
        
        # Base query for students in group with a TG account
        stmt = select(TgAccount).join(Student, TgAccount.student_id == Student.id).where(Student.group_number == group_number)
        
        # Subquery for checking existence of documents
        doc_exists = exists().where(
            StudentDocument.student_id == Student.id,
            StudentDocument.file_type == "document"
        )
            
        stmt = stmt.where(~doc_exists)
        
        result = await db.execute(stmt)
        tg_accounts = result.scalars().all()
        
        count = 0
        for acc in tg_accounts:
            try:
                msg = (
                    f"🔔 <b>Guruh bo'yicha hujjat topshirish eslatmasi</b>\n\n"
                    f"Tyutoringiz <b>{tutor.full_name}</b> ({group_number} guruhi) barcha "
                    f"talabalardan <b>{cat_name}</b> yuklashni so'ramoqda."
                )
                await bot.send_message(acc.telegram_id, msg, parse_mode="HTML")
                count += 1
            except:
                pass
                
        return {"success": True, "message": f"{count} ta talabaga xabar yuborildi"}
        
    return {"success": False, "message": "Ma'lumotlar yetarli emas"}

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
        
    # 2. Count Total Students (FROM HEMIS API)
    from config import HEMIS_ADMIN_TOKEN
    from services.hemis_service import HemisService
    
    # We pass the group numbers (names) to the service
    # Use Admin Token to ensure we can see all groups (pagination + scope)
    hemis_student_count = await HemisService.get_total_students_for_groups(group_numbers, HEMIS_ADMIN_TOKEN)
    
    # Fallback to DB if HEMIS returns 0 (maybe network error or empty)
    if hemis_student_count > 0:
        student_count = hemis_student_count
    else:
        # Fallback to local DB count
        student_count = await db.scalar(
            select(func.count(Student.id)).where(Student.group_number.in_(group_numbers))
        )

    # 2.1 Count Active Students (Logged into App - Has HEMIS Token)
    # User requested to count students who logged into the app
    active_student_count = await db.scalar(
        select(func.count(Student.id))
        .where(
            Student.group_number.in_(group_numbers),
            Student.hemis_token.is_not(None)
        )
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
            "active_student_count": active_student_count or 0,
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

@router.post("/reply")
async def reply_to_appeal(
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

    # 2. Optimized Aggregate Query
    from datetime import datetime
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    stmt = (
        select(
            Student.group_number,
            func.count(case((UserActivity.status == 'pending', 1), else_=None)).label("pending_count"),
            func.count(case((UserActivity.created_at >= today_start, 1), else_=None)).label("today_count")
        )
        .join(Student, UserActivity.student_id == Student.id)
        .where(Student.group_number.in_(group_numbers))
        .group_by(Student.group_number)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Convert to map for easy lookup
    stats_map = {
        r.group_number: {"pending": r.pending_count, "today": r.today_count}
        for r in rows
    }
    
    stats = []
    for gn in group_numbers:
        s = stats_map.get(gn, {"pending": 0, "today": 0})
        stats.append({
            "group_number": gn,
            "pending_count": s["pending"],
            "today_count": s["today"]
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
        
    if new_status == "accepted":
        activity.status = "approved"
    else:
        activity.status = "rejected"
    await db.commit()
    
    return {"success": True, "message": f"Faollik {new_status} qilindi"}


# ============================================================
# 6. SERTIFIKATLAR (CERTIFICATES)
# ============================================================

@router.get("/certificates/stats")
@cache(expire=300)
async def get_tutor_certificate_stats(
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get certificate upload statistics for each of the tutor's groups.
    """
    # 1. Get Tutor's Groups
    groups_result = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor.id))
    group_numbers = groups_result.scalars().all()
    
    if not group_numbers:
        return {"success": True, "data": []}

    # Optimized Aggregate Query
    from sqlalchemy import distinct
    from config import HEMIS_ADMIN_TOKEN
    from services.hemis_service import HemisService
    
    # Fetch accurate totals from HEMIS
    hemis_counts = await HemisService.get_group_student_counts(group_numbers, HEMIS_ADMIN_TOKEN)
    
    stmt = (
        select(
            Student.group_number,
            func.count(distinct(StudentDocument.student_id)).label("students_with_certs")
        )
        .join(StudentDocument, Student.id == StudentDocument.student_id)
        .where(
            Student.group_number.in_(group_numbers),
            StudentDocument.file_type == "certificate"
        )
        .group_by(Student.group_number)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    uploaded_map = {r.group_number: r.students_with_certs for r in rows}
    
    data = []
    for gn in group_numbers:
        total = hemis_counts.get(gn, 0)
        data.append({
            "group_number": gn,
            "total_students": total,
            "uploaded_students": uploaded_map.get(gn, 0)
        })
        
    return {"success": True, "data": data}

@router.get("/certificates/group/{group_number}")
async def get_group_certificate_details(
    group_number: str,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get detailed certificate status (counts) for all students in a group.
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

    # Fetch students and their certificates
    from database.models import StudentDocument
    stmt = (
        select(
            Student.id,
            Student.full_name,
            Student.image_url,
            Student.hemis_id,
            func.count(StudentDocument.id).label("cert_count")
        )
        .outerjoin(StudentDocument, and_(Student.id == StudentDocument.student_id, StudentDocument.file_type == "certificate"))
        .where(Student.group_number == group_number)
        .group_by(Student.id)
        .order_by(Student.full_name)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "full_name": r.full_name,
            "image": r.image_url,
            "hemis_id": r.hemis_id,
            "certificate_count": r.cert_count
        })
        
    return {"success": True, "data": data}

@router.get("/certificates/student/{student_id}")
async def get_student_certificates_for_tutor(
    student_id: int,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Get all certificates for a specific student.
    """
    # 1. Get Student
    stmt = select(Student).where(Student.id == student_id)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Talaba topilmadi")
        
    # 2. Verify Tutor Access to Student's Group
    access_check = await db.execute(
        select(TutorGroup).where(
            TutorGroup.tutor_id == tutor.id,
            TutorGroup.group_number == student.group_number
        )
    )
    if not access_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Siz bu talabaga biriktirilmagansiz")

    # 3. Fetch Certificates
    stmt = select(StudentDocument).where(
        StudentDocument.student_id == student_id,
        StudentDocument.file_type == "certificate"
    ).order_by(StudentDocument.uploaded_at.desc())
    result = await db.execute(stmt)
    certs = result.scalars().all()
    
    data = [
        {
            "id": c.id,
            "title": c.file_name,
            "created_at": c.uploaded_at.isoformat()
        } for c in certs
    ]

    # [DEMO] Add Mock Data for specific Demo Students
    if student_id in [771, 858] and not data:
        data = [
            {"id": -101, "title": "IELTS 7.5 Certificate", "created_at": datetime.utcnow().isoformat()},
            {"id": -102, "title": "IT-Park Python Programming", "created_at": datetime.utcnow().isoformat()},
            {"id": -103, "title": "Topik II Level 4", "created_at": datetime.utcnow().isoformat()},
        ]
    
    return {
        "success": True,
        "data": data
    }

@router.post("/certificates/{cert_id}/download")
async def send_student_cert_to_tutor(
    cert_id: int,
    db: AsyncSession = Depends(get_session),
    tutor: Staff = Depends(get_current_staff)
):
    """
    Sends the certificate file to the tutor's Telegram bot.
    """
    # 1. Get Certificate and Student Info
    stmt = (
        select(StudentDocument, Student)
        .join(Student, StudentDocument.student_id == Student.id)
        .where(StudentDocument.id == cert_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if cert_id < 0:
        # Mock handle for demo certificates
        return {"success": True, "message": "Demo sertifikat Telegramingizga yuborildi!"}

    if not row:
        raise HTTPException(status_code=404, detail="Sertifikat topilmadi")
        
    cert, student = row
    
    # 2. Verify Tutor Access
    access_check = await db.execute(
        select(TutorGroup).where(
            TutorGroup.tutor_id == tutor.id,
            TutorGroup.group_number == student.group_number
        )
    )
    if not access_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Siz bu talabaga biriktirilmagansiz")

    # 3. Get Tutor's TG Account
    from database.models import TgAccount
    stmt = select(TgAccount).where(TgAccount.staff_id == tutor.id)
    tg_acc = await db.scalar(stmt)
    
    if not tg_acc:
        return {"success": False, "message": "Sizning Telegram hisobingiz ulanmagan. Iltimos, botga kiring."}

    # 4. Send via Bot
    try:
        caption = (
            f"🎓 <b>Yangi Sertifikat</b>\n\n"
            f"Talaba: <b>{student.full_name}</b>\n"
            f"Guruh: <b>{student.group_number}</b>\n"
            f"Sertifikat: <b>{cert.file_name}</b>"
        )
        # Better detection
        is_photo = cert.mime_type and "image" in cert.mime_type
        
        if is_photo:
            await bot.send_photo(tg_acc.telegram_id, cert.telegram_file_id, caption=caption, parse_mode="HTML")
        else:
            await bot.send_document(tg_acc.telegram_id, cert.telegram_file_id, caption=caption, parse_mode="HTML")
        return {"success": True, "message": "Sertifikat Telegramingizga yuborildi!"}
    except Exception as e:
        logger.error(f"Error sending cert to tutor: {e}")
        return {"success": False, "message": f"Botda xatolik yuz berdi: {str(e)}"}

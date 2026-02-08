from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Dict, Any

from api.dependencies import get_current_student, get_db
from database.models import Student, Staff, TgAccount, UserActivity
from database.models import StaffRole
from services.analytics_service import get_management_analytics
from services.ai_service import generate_answer_by_key
from data.ai_prompts import AI_PROMPTS
import json

router = APIRouter(prefix="/management", tags=["Management"])

@router.get("/dashboard")
async def get_management_dashboard(
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get university-wide statistics for management dashboard.
    """
    # 1. Role Check (Explicit for Rahbariyat)
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    uni_id = getattr(staff, 'university_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    from services.hemis_service import HemisService
    
    token = getattr(staff, 'hemis_token', None)
    total_students_api = 0
    if token:
        total_students_api = await HemisService.get_total_student_count(token)

    # 2. Total Students in University
    # Priority: API -> DB (Fallback)
    if total_students_api > 0:
        total_students = total_students_api
    else:
        total_students = await db.scalar(
            select(func.count(Student.id)).where(Student.university_id == uni_id)
        ) or 0

    # 3. Platform Users (Students who have logged in - have hemis_token)
    platform_users = await db.scalar(
        select(func.count(Student.id))
        .where(Student.university_id == uni_id, Student.hemis_token != None)
    ) or 0

    # 4. Total Staff in University
    total_staff = await db.scalar(
        select(func.count(Staff.id)).where(Staff.university_id == uni_id)
    ) or 0

    # 5. Additional Metrics (Placeholders for now as per previous logic)
    # debtor_count and avg_gpa can be calculated or mocked if not yet synced university-wide
    # For now, let's provide realistic counts
    
    # 6. Calc Usage Percentage
    usage_percentage = 0
    if total_students > 0:
        usage_percentage = round((platform_users / total_students) * 100)

    return {
        "success": True,
        "data": {
            "student_count": total_students,
            "platform_users": platform_users,
            "usage_percentage": usage_percentage,
            "staff_count": total_staff,
            "university_name": getattr(staff, 'university_name', "Universitet")
        }
    }

@router.get("/faculties")
async def get_mgmt_faculties(
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Security & Context
    uni_id = getattr(staff, 'university_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # Show only faculties that have students AND a name
    result = await db.execute(
        select(Student.faculty_id, Student.faculty_name)
        .where(
            Student.university_id == uni_id, 
            Student.faculty_id != None,
            Student.faculty_name != None
        )
        .distinct()
        .order_by(Student.faculty_name)
    )
    faculties_data = result.all()
    
    return {
        "success": True, 
        "data": [{"id": f[0], "name": f[1]} for f in faculties_data]
    }

@router.get("/faculties/{faculty_id}/levels")
async def get_mgmt_levels(
    faculty_id: int,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Security: Ensure faculty belongs to staff's university
    uni_id = getattr(staff, 'university_id', None)
    
    # Unique levels for this faculty
    result = await db.execute(
        select(Student.level_name)
        .where(Student.faculty_id == faculty_id, Student.university_id == uni_id)
        .distinct()
        .order_by(Student.level_name)
    )
    levels = [r for r in result.scalars().all() if r]
    return {"success": True, "data": levels}

@router.get("/faculties/{faculty_id}/levels/{level_name}/groups")
async def get_mgmt_groups(
    faculty_id: int,
    level_name: str,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Security
    uni_id = getattr(staff, 'university_id', None)

    # Unique groups for this faculty and level
    result = await db.execute(
        select(Student.group_number)
        .where(
            Student.faculty_id == faculty_id, 
            Student.level_name == level_name,
            Student.university_id == uni_id
        )
        .distinct()
        .order_by(Student.group_number)
    )
    groups = [r for r in result.scalars().all() if r]
    return {"success": True, "data": groups}

@router.get("/groups/{group_number}/students")
async def get_mgmt_group_students(
    group_number: str,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    # Security
    uni_id = getattr(staff, 'university_id', None)

    result = await db.execute(
        select(Student)
        .where(Student.group_number == group_number, Student.university_id == uni_id)
        .order_by(Student.full_name)
    )
    students = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": s.id, 
                "full_name": s.full_name, 
                "hemis_id": s.hemis_id,
                "hemis_login": s.hemis_login,
                "image_url": s.image_url
            } for s in students
        ]
    }

@router.get("/students/search")
async def search_mgmt_students(
    query: str = None,
    faculty_id: int = None,
    education_type: str = None,
    education_form: str = None,
    level_name: str = None,
    specialty_name: str = None,
    group_number: str = None,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    uni_id = getattr(staff, 'university_id', None)
    if uni_id is None:
        return {"success": True, "total_count": 0, "app_users_count": 0, "data": []}
    
    # 1. Base category filters (University + Dropdowns)
    category_filters = [Student.university_id == uni_id]
    if faculty_id: category_filters.append(Student.faculty_id == faculty_id)
    if education_type: category_filters.append(Student.education_type == education_type)
    if education_form: category_filters.append(Student.education_form == education_form)
    if level_name: category_filters.append(Student.level_name == level_name)
    if specialty_name: category_filters.append(Student.specialty_name == specialty_name)
    if group_number: category_filters.append(Student.group_number == group_number)

    # 2. Search filters (Dropdowns + Query)
    search_filters = list(category_filters)
    if query:
        search_filters.append(
            (Student.full_name.ilike(f"%{query}%")) | 
            (Student.hemis_id.ilike(f"%{query}%")) |
            (Student.hemis_login.ilike(f"%{query}%"))
        )

    # 3. Get Students (using Search filters)
    stmt = select(Student).where(and_(*search_filters)).order_by(Student.full_name).limit(500)
    result = await db.execute(stmt)
    students = result.scalars().all()
    
    # 4. Get Stats (using Category filters)
    # Total Count in category
    count_stmt = select(func.count(Student.id)).where(and_(*category_filters))
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    # App Users Count in category (Students with TG account)
    from sqlalchemy import distinct
    app_users_stmt = select(func.count(distinct(Student.id))).join(TgAccount).where(and_(*category_filters))
    app_users_count = (await db.execute(app_users_stmt)).scalar() or 0
    
    return {
        "success": True, 
        "total_count": total_count,
        "app_users_count": app_users_count,
        "data": [
            {
                "id": s.id, 
                "full_name": s.full_name, 
                "hemis_id": s.hemis_id,
                "hemis_login": s.hemis_login,
                "image_url": s.image_url,
                "group_number": s.group_number,
                "faculty_name": s.faculty_name,
                "specialty_name": s.specialty_name,
                "level_name": s.level_name,
                "education_form": s.education_form
            } for s in students
        ]
    }

@router.get("/specialties")
async def get_mgmt_specialties(
    faculty_id: int = None,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    uni_id = getattr(staff, 'university_id', None)
    
    stmt = select(Student.specialty_name).where(
        Student.university_id == uni_id, 
        Student.specialty_name != None
    )
    
    if faculty_id:
        stmt = stmt.where(Student.faculty_id == faculty_id)
        
    result = await db.execute(stmt.distinct().order_by(Student.specialty_name))
    specialties = result.scalars().all()
    
    return {"success": True, "data": specialties}

@router.get("/groups")
async def get_mgmt_groups(
    faculty_id: int = None,
    level_name: str = None,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    uni_id = getattr(staff, 'university_id', None)
    
    stmt = select(Student.group_number).where(
        Student.university_id == uni_id, 
        Student.group_number != None
    )
    
    if faculty_id: stmt = stmt.where(Student.faculty_id == faculty_id)
    if level_name: stmt = stmt.where(Student.level_name == level_name)
        
    result = await db.execute(stmt.distinct().order_by(Student.group_number))
    groups = result.scalars().all()
    
    return {"success": True, "data": groups}

@router.get("/students/{student_id}/full-details")
async def get_mgmt_student_details(
    student_id: int,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    try:
        from database.models import UserActivity, UserDocument, UserCertificate, StudentFeedback
        
        student = await db.get(Student, student_id)
        if not student: raise HTTPException(status_code=404, detail="Talaba topilmadi")

        # Security: Ensure student belongs to staff's university
        uni_id = getattr(staff, 'university_id', None)
        if student.university_id != uni_id:
            raise HTTPException(status_code=403, detail="Boshqa universitet talabasi ma'lumotlarini ko'rish imkonsiz")

        # 1. Appeals (Feedbacks) - parent_id=None are top-level threads
        appeals_result = await db.execute(
            select(StudentFeedback)
            .where(StudentFeedback.student_id == student_id, StudentFeedback.parent_id == None)
            .order_by(StudentFeedback.created_at.desc())
        )
        appeals = appeals_result.scalars().all()

        # 2. Activities (With Images Eagerly Loaded)
        activities_result = await db.execute(
            select(UserActivity)
            .where(UserActivity.student_id == student_id)
            .options(selectinload(UserActivity.images))
            .order_by(UserActivity.created_at.desc())
        )
        activities = activities_result.scalars().all()

        # 3. Documents
        docs_result = await db.execute(
            select(UserDocument)
            .where(UserDocument.student_id == student_id)
            .order_by(UserDocument.created_at.desc())
        )
        docs = docs_result.scalars().all()

        # 4. Certificates
        certs_result = await db.execute(
            select(UserCertificate)
            .where(UserCertificate.student_id == student_id)
            .order_by(UserCertificate.created_at.desc())
        )
        certs = certs_result.scalars().all()

        def safe_isoformat(dt):
            if not dt: return None
            if isinstance(dt, str): return dt
            try:
                return dt.isoformat()
            except:
                return str(dt)

        return {
            "success": True,
            "data": {
                "profile": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "hemis_id": getattr(student, 'hemis_id', None),
                    "hemis_login": getattr(student, 'hemis_login', None),
                    "faculty_name": getattr(student, 'faculty_name', None),
                    "group_number": getattr(student, 'group_number', None),
                    "image_url": getattr(student, 'image_url', None),
                    "phone": getattr(student, 'phone', None),
                    "gpa": getattr(student, 'gpa', 0.0)
                },
                "appeals": [
                    {
                        "id": a.id, 
                        "text": a.text, 
                        "status": getattr(a, 'status', 'pending'), 
                        "date": safe_isoformat(getattr(a, 'created_at', None)),
                        "file_id": getattr(a, 'file_id', None),
                        "file_type": getattr(a, 'file_type', 'photo')
                    } for a in appeals
                ],
                "activities": [
                    {
                        "id": act.id, 
                        "title": getattr(act, 'name', getattr(act, 'title', 'Benoq')), 
                        "status": getattr(act, 'status', 'pending'), 
                        "date": safe_isoformat(getattr(act, 'created_at', None)),
                        "images": [{"file_id": img.file_id, "file_type": img.file_type} for img in getattr(act, 'images', [])]
                    } for act in activities
                ],
                "documents": [
                    {
                        "id": d.id, 
                        "title": d.title, 
                        "status": getattr(d, 'status', 'pending'), 
                        "date": safe_isoformat(getattr(d, 'created_at', None)),
                        "file_id": getattr(d, 'file_id', None),
                        "file_type": getattr(d, 'file_type', 'document')
                    } for d in docs
                ],
                "certificates": [
                    {
                        "id": c.id, 
                        "title": c.title, 
                        "status": "active", 
                        "date": safe_isoformat(getattr(c, 'created_at', None)),
                        "file_id": getattr(c, 'file_id', None)
                    } for c in certs
                ]
            }
        }
    except Exception as e:
        import traceback
        print(f"ERROR in get_mgmt_student_details: {e}")
        traceback.print_exc()
        return {"success": False, "message": str(e)}

@router.get("/analytics")
async def get_mgmt_analytics(
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get holistic analytics for the Rahbariyat dashboard.
    """
    # Security
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
    stats = await get_management_analytics(db)
    return {"success": True, "data": stats}

@router.get("/ai-report")
async def get_mgmt_ai_report(
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate an AI report based on current university stats.
    """
    # Security
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
    
    # 1. Get Stats
    stats = await get_management_analytics(db)
    
    # 2. Format Context
    stats_str = json.dumps(stats, indent=2, ensure_ascii=False)
    
    # 3. Generate Report
    prompt_template = AI_PROMPTS.get("management_report")
    if not prompt_template:
        return {"success": False, "message": "AI buyrug'i (prompt) topilmadi"}
        
    final_prompt = prompt_template.format(stats_context=stats_str)
    
    # We use 'management_report' key to maybe select model if logic changes, 
    # but we pass custom_prompt so it overrides the default lookup.
    ai_response = await generate_answer_by_key("management_report", custom_prompt=final_prompt)
    
    return {"success": True, "data": ai_response}

@router.post("/certificates/{cert_id}/download")
async def send_student_cert_to_management(
    cert_id: int,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends the certificate file to the management user's Telegram bot.
    """
    from database.models import UserCertificate
    from bot import bot
    
    # Security
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
    
    # 1. Get Certificate and Student Info
    stmt = (
        select(UserCertificate, Student)
        .join(Student, UserCertificate.student_id == Student.id)
        .where(UserCertificate.id == cert_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Sertifikat topilmadi")
        
    cert, student = row
    
    # 2. Verify Management Access (University Check)
    uni_id = getattr(staff, 'university_id', None)
    if student.university_id != uni_id:
        raise HTTPException(status_code=403, detail="Boshqa universitet talabasi ma'lumotlarini yuklash imkonsiz")

    # 3. Get Management User's TG Account
    # 'staff' variable can be Student or Staff model instance
    tg_acc = await db.scalar(select(TgAccount).where(
        (TgAccount.student_id == staff.id) | (TgAccount.staff_id == staff.id)
    ))
    
    if not tg_acc:
        # Try to find by telegram_id in token if available? No, token data is strict.
        return {"success": False, "message": "Sizning Telegram hisobingiz ulanmagan. Iltimos, botga kiring."}

    # 4. Send via Bot
    try:
        caption = (
            f"🎓 <b>Talaba Sertifikati (Rahbariyat)</b>\n\n"
            f"Talaba: <b>{student.full_name}</b>\n"
            f"Guruh: <b>{student.group_number}</b>\n"
            f"Sertifikat: <b>{cert.title}</b>"
        )
        # TEST: Hardcoded ID 7476703866
        await bot.send_document(7476703866, cert.file_id, caption=caption, parse_mode="HTML")
        return {"success": True, "message": "Sertifikat Telegramingizga yuborildi (TEST ID: 7476703866)!"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending cert to management: {e}")
        return {"success": False, "message": f"Botda xatolik yuz berdi: {str(e)}"}

@router.post("/documents/{doc_id}/download")
async def send_student_doc_to_management(
    doc_id: int,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends the document file to the management user's Telegram bot.
    """
    from database.models import UserDocument
    from bot import bot
    
    # Security
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
    
    # 1. Get Document and Student Info
    stmt = (
        select(UserDocument, Student)
        .join(Student, UserDocument.student_id == Student.id)
        .where(UserDocument.id == doc_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
        
    doc, student = row
    
    # 2. Verify Management Access (University Check)
    uni_id = getattr(staff, 'university_id', None)
    if student.university_id != uni_id:
        raise HTTPException(status_code=403, detail="Boshqa universitet talabasi ma'lumotlarini yuklash imkonsiz")

    # 3. Get Management User's TG Account
    tg_acc = await db.scalar(select(TgAccount).where(
        (TgAccount.student_id == staff.id) | (TgAccount.staff_id == staff.id)
    ))
    
    if not tg_acc:
        return {"success": False, "message": "Sizning Telegram hisobingiz ulanmagan. Iltimos, botga kiring."}

    # 4. Send via Bot
    try:
        caption = (
            f"📄 <b>Talaba Hujjati (Rahbariyat)</b>\n\n"
            f"Talaba: <b>{student.full_name}</b>\n"
            f"Guruh: <b>{student.group_number}</b>\n"
            f"Hujjat: <b>{doc.title}</b>\n"
            f"Kategoriya: <b>{doc.category}</b>"
        )
        # TEST: Hardcoded ID 7476703866
        if doc.file_type == 'photo':
             await bot.send_photo(7476703866, doc.file_id, caption=caption, parse_mode="HTML")
        else:
             await bot.send_document(7476703866, doc.file_id, caption=caption, parse_mode="HTML")
             
        return {"success": True, "message": "Hujjat Telegramingizga yuborildi (TEST ID: 7476703866)!"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending doc to management: {e}")
        return {"success": False, "message": f"Botda xatolik yuz berdi: {str(e)}"}

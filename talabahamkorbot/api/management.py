from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List
import zipfile
import io
import aiohttp

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
    # 2. Filter by Faculty if restricted
    f_id = getattr(staff, 'faculty_id', None)
    
    # Priority: API -> DB (Fallback)
    # If Dean, avoid API for now as it might return global counts or requires complex faculty-specific API calls
    if f_id:
        total_students = await db.scalar(
            select(func.count(Student.id)).where(Student.university_id == uni_id, Student.faculty_id == f_id)
        ) or 0
        platform_users = await db.scalar(
            select(func.count(Student.id))
            .where(Student.university_id == uni_id, Student.faculty_id == f_id, Student.hemis_token != None)
        ) or 0
        total_staff = await db.scalar(
            select(func.count(Staff.id)).where(Staff.university_id == uni_id, Staff.faculty_id == f_id)
        ) or 0
    else:
        # Global Management
        if total_students_api > 0:
            total_students = total_students_api
        else:
            total_students = await db.scalar(
                select(func.count(Student.id)).where(Student.university_id == uni_id)
            ) or 0

        platform_users = await db.scalar(
            select(func.count(Student.id))
            .where(Student.university_id == uni_id, Student.hemis_token != None)
        ) or 0

        public_employees = await HemisService.get_public_employee_count()
        if public_employees > 0:
            total_staff = public_employees
        else:
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

    # 1. Try to fetch official faculties from HEMIS (Admin Token)
    from services.hemis_service import HemisService
    from config import HEMIS_ADMIN_TOKEN
    
    f_id = getattr(staff, 'faculty_id', None)
    
    if HEMIS_ADMIN_TOKEN:
        faculties = await HemisService.get_faculties()
        if faculties:
             # Filter only specific faculties for this University structure
             allowed_ids = [4, 2, 43]
             filtered = [f for f in faculties if f['id'] in allowed_ids]
             
             if f_id:
                 # Resolve if our faculty_id matches one of these
                 # Check by name matching if id doesn't align (some IDs are internal)
                 # But usually we map HEMIS IDs to our faculty_id during import
                 # Let's trust local DB if f_id is set
                 pass 
             else:
                 return {"success": True, "data": filtered}

    # 2. Local DB Lookup (Respect restricted f_id)
    stmt = (
        select(Student.faculty_id, Student.faculty_name)
        .where(
            Student.university_id == uni_id, 
            Student.faculty_id != None,
            Student.faculty_name != None
        )
    )
    if f_id:
        stmt = stmt.where(Student.faculty_id == f_id)
        
    result = await db.execute(stmt.distinct().order_by(Student.faculty_name))
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
    f_id = getattr(staff, 'faculty_id', None)
    
    if f_id and f_id != faculty_id:
        raise HTTPException(status_code=403, detail="Sizga boshqa fakultet ma'lumotlari ruxsat berilmagan")
    
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
    f_id = getattr(staff, 'faculty_id', None)
    
    if f_id and f_id != faculty_id:
        raise HTTPException(status_code=403, detail="Sizga boshqa fakultet ma'lumotlari ruxsat berilmagan")

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
    f_id = getattr(staff, 'faculty_id', None)

    stmt = select(Student).where(Student.group_number == group_number, Student.university_id == uni_id)
    if f_id:
        stmt = stmt.where(Student.faculty_id == f_id)

    result = await db.execute(stmt.order_by(Student.full_name))
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

def calculate_public_filtered_count(
    stats: Dict[str, Any], 
    education_type: str = None, 
    education_form: str = None, 
    level: str = None
) -> int:
    """
    Calculates the total student count from public stats JSON based on filters.
    """
    if not stats: return 0
    
    # Normalize inputs
    if education_type == "Bakalavr": p_type = "Bakalavr"
    elif education_type == "Magistr": p_type = "Magistr"
    else: p_type = None

    # 1. Drill by Level (Most granular combination available)
    if level:
        levels_data = stats.get("level", {})
        count = 0
        types_to_check = [p_type] if p_type else ["Bakalavr", "Magistr"]
        
        for t in types_to_check:
            type_data = levels_data.get(t, {})
            level_data = type_data.get(level, {})
            if level_data:
                 if education_form:
                     count += level_data.get(education_form, 0)
                 else:
                     # Sum all forms for this level
                     for form_val in level_data.values():
                         if isinstance(form_val, int): count += form_val
        return count

    # 2. Drill by Education Form (If no level)
    if education_form:
        forms_data = stats.get("education_form", {})
        count = 0
        types_to_check = [p_type] if p_type else ["Bakalavr", "Magistr"]
        
        for t in types_to_check:
            type_data = forms_data.get(t, {})
            form_data = type_data.get(education_form, {})
            if isinstance(form_data, dict):
                count += form_data.get("Erkak", 0) + form_data.get("Ayol", 0)
        return count

    # 3. Drill by Education Type only
    if p_type:
        type_stats = stats.get("education_type", {}).get(p_type, {})
        return type_stats.get("Erkak", 0) + type_stats.get("Ayol", 0)

    # 4. Fallback: Total
    jami = stats.get("education_type", {}).get("Jami", {})
    return jami.get("Erkak", 0) + jami.get("Ayol", 0)

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
    # Custom Faculty ID Mapping for Local DB (Admin to Local)
    db_faculty_id = faculty_id
    if faculty_id == 4: db_faculty_id = 36   # Jurnalistika
    elif faculty_id == 2: db_faculty_id = 34 # PR
    elif faculty_id == 43: db_faculty_id = 35 # Xalqaro
    
    if db_faculty_id: category_filters.append(Student.faculty_id == db_faculty_id)
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
    
    # 4. Get Stats
    from services.hemis_service import HemisService
    
    # Check if we have Admin Token configured
    from config import HEMIS_ADMIN_TOKEN
    
    if HEMIS_ADMIN_TOKEN:
        # Use Admin API for ALL filters if token is available (most accurate method)
        admin_filters = {}
        
        # --- CUSTOM LOGIC FOR THIS UNIVERSITY ---
        # 1. Handle Magistr -> Department 36 (Magistratura bo'limi)
        start_dept_override = False
        if education_type and "Magistr" in education_type:
             admin_filters["_department"] = 36
             start_dept_override = True
             
        # 2. Handle Sirtqi -> Department 35 (Sirtqi bo'limi)
        # Note: If both Magistr and Sirtqi are selected (unlikely combo), Sirtqi overrides here or vice versa.
        # Let's prioritize Magistr if present, else Sirtqi.
        if not start_dept_override and education_form and "Sirtqi" in education_form:
             admin_filters["_department"] = 35
             start_dept_override = True

        # 3. Standard Faculty Filter (only if not overridden)
        if not start_dept_override and faculty_id:
            admin_filters["_department"] = faculty_id
            
        if education_type and not start_dept_override:
            # Standard Education Type mapping
            if "Bakalavr" in education_type:
                admin_filters["_education_type"] = 11
            elif "Magistr" in education_type:
                admin_filters["_education_type"] = 12
            else:
                # Fallback: try to pass as is or map other types if known
                # But for now, user only complained about Bakalavr.
                pass

        if specialty_name:
            # Resolve ID from DB
            spec_stmt = select(Student.specialty_id).where(Student.specialty_name == specialty_name).limit(1)
            spec_id = (await db.execute(spec_stmt)).scalar()
            if spec_id:
                admin_filters["_specialty"] = spec_id
                
        if group_number:
            # Resolve ID from DB
            grp_stmt = select(Student.group_id).where(Student.group_number == group_number).limit(1)
            grp_id = (await db.execute(grp_stmt)).scalar()
            if grp_id:
                admin_filters["_group"] = grp_id
        
        # Fetch from Admin API
        # Note: If no filters are passed, it returns total university count (which is good)
        total_count = await HemisService.get_admin_student_count(admin_filters)
        
        # If Admin API fails (cnt=0) and we have no filters, it might be an error or just empty.
        # If it returns 0 but DB has users, we might want to fallback to DB count?
        # But valid answer could be 0 (e.g. empty group).
        # Let's trust Admin API if it returns success (handled in service), but if 0, maybe check DB?
        # The service returns 0 on error.
        
        if total_count == 0:
             # Fallback to DB if API failed or returned 0 (and we suspect it's wrong)
             # But if it's a specific filter, 0 might be correct.
             # Let's assume if it's 0, we fallback to DB count just in case API token is bad.
             count_stmt = select(func.count(Student.id)).where(and_(*category_filters))
             db_count = (await db.execute(count_stmt)).scalar() or 0
             total_count = max(total_count, db_count)

    else:
        # Fallback to Old Logic (Public API + DB)
        has_backend_filters = any([faculty_id, specialty_name, group_number])
        
        if not has_backend_filters:
            public_stats = await HemisService.get_public_stats()
            total_count = calculate_public_filtered_count(
                public_stats,
                education_type=education_type,
                education_form=education_form,
                level=level_name
            )
        else:
            # Use DB Count for specific filters
            count_stmt = select(func.count(Student.id)).where(and_(*category_filters))
            total_count = (await db.execute(count_stmt)).scalar() or 0

    # App Users Count (Students who logged into app - always DB)

    # App Users Count (Students who logged into app - always DB)
    app_users_stmt = select(func.count(Student.id)).where(
        and_(*search_filters), # Use exact search filters for app users
        Student.hemis_token != None
    )
    app_users_count = (await db.execute(app_users_stmt)).scalar() or 0
    
    # Final check: if total_count is 0 but we have students in DB, use DB count
    # (Happens for extremely granular queries that public stats don't cover)
    if total_count == 0:
        count_stmt = select(func.count(Student.id)).where(and_(*search_filters))
        total_count = (await db.execute(count_stmt)).scalar() or 0

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

@router.get("/staff/search")
async def search_mgmt_staff(
    query: str = None,
    faculty_id: int = None,
    role: str = None,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Search and filter university staff members with activity status.
    """
    # Security Check
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # If restricted, force search within faculty
    if f_id:
        faculty_id = f_id

    # Base query with unique constraint for scalars()
    stmt = (
        select(Staff)
        .where(Staff.university_id == uni_id)
        .options(selectinload(Staff.tg_accounts))
        .options(selectinload(Staff.faculty)) # Loading faculty name if needed
    )
    
    # Filters
    if faculty_id:
        stmt = stmt.where(Staff.faculty_id == faculty_id)
    if role:
        stmt = stmt.where(Staff.role == role)
    if query:
        stmt = stmt.where(
            (Staff.full_name.ilike(f"%{query}%")) | 
            (Staff.position.ilike(f"%{query}%")) |
            (Staff.department.ilike(f"%{query}%"))
        )
    
    stmt = stmt.order_by(Staff.full_name)

    result = await db.execute(stmt)
    staff_items = result.scalars().unique().all()
    
    def get_last_active(s: Staff):
        if not s.tg_accounts: return None
        actives = [t.last_active for t in s.tg_accounts if t.last_active]
        return max(actives).isoformat() if actives else None

    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "full_name": s.full_name,
                "role": s.role,
                "position": s.position,
                "department": s.department,
                "faculty_name": s.faculty.name if s.faculty else None,
                "image_url": s.image_url,
                "last_active": get_last_active(s)
            } for s in staff_items
        ]
    }

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
        print(f"DEBUG: Attempting to send document {doc.id} to user 7476703866")
        caption = (
            f"📄 <b>Talaba Hujjati (Rahbariyat)</b>\n\n"
            f"Talaba: <b>{student.full_name}</b>\n"
            f"Guruh: <b>{student.group_number}</b>\n"
            f"Hujjat: <b>{doc.title}</b>\n"
            f"Kategoriya: <b>{doc.category}</b>"
        )
        # TEST: Hardcoded ID 7476703866
        if doc.file_type == 'photo':
             print(f"DEBUG: Sending photo {doc.file_id}")
             await bot.send_photo(7476703866, doc.file_id, caption=caption, parse_mode="HTML")
        else:
             print(f"DEBUG: Sending document {doc.file_id}")
             await bot.send_document(7476703866, doc.file_id, caption=caption, parse_mode="HTML")
             
        print("DEBUG: Successfully sent document")
        return {"success": True, "message": "Hujjat Telegramingizga yuborildi (TEST ID: 7476703866)!"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Error sending doc: {e}")
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending doc to management: {e}")
        return {"success": False, "message": f"Botda xatolik yuz berdi: {str(e)}"}

@router.get("/documents/archive")
async def get_mgmt_documents_archive(
    query: str = None,
    faculty_id: int = None,
    title: str = None,
    education_type: str = None,
    education_form: str = None,
    level_name: str = None,
    specialty_name: str = None,
    group_number: str = None,
    page: int = 1,
    limit: int = 50,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all student documents for management with filtering.
    """
    from database.models import UserDocument
    
    # 1. Security Check
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
    uni_id = getattr(staff, 'university_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # 1. Base category filters (University + Dropdowns)
    category_filters = [Student.university_id == uni_id]
    if faculty_id: category_filters.append(Student.faculty_id == faculty_id)
    if education_type: category_filters.append(Student.education_type == education_type)
    if education_form: category_filters.append(Student.education_form == education_form)
    if level_name: category_filters.append(Student.level_name == level_name)
    if specialty_name: category_filters.append(Student.specialty_name == specialty_name)
    if group_number: category_filters.append(Student.group_number == group_number)

    # 2. Build Query for Documents
    stmt = (
        select(UserDocument, Student)
        .join(Student, UserDocument.student_id == Student.id)
        .where(and_(*category_filters))
    )

    if title:
        stmt = stmt.where(UserDocument.title == title)
        
    if query:
        stmt = stmt.where(
            (Student.full_name.ilike(f"%{query}%")) |
            (UserDocument.title.ilike(f"%{query}%"))
        )

    # 3. Pagination & Execution
    stmt = stmt.order_by(UserDocument.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    # 4. Get Stats (Matching Student Search logic)
    has_backend_filters = any([faculty_id, specialty_name, group_number])
    
    if not has_backend_filters:
        from services.hemis_service import HemisService
        public_stats = await HemisService.get_public_stats()
        
        total_count = calculate_public_filtered_count(
            public_stats,
            education_type=education_type,
            education_form=education_form,
            level=level_name
        )
    else:
        # Use DB Count for specific filters
        count_stmt = select(func.count(Student.id)).where(and_(*category_filters))
        total_count = (await db.execute(count_stmt)).scalar() or 0

    # App Users Count (Students who logged into app - always DB)
    app_users_stmt = select(func.count(Student.id)).where(
        and_(*category_filters),
        Student.hemis_token != None
    )
    app_users_count = (await db.execute(app_users_stmt)).scalar() or 0
    
    # Fallback for total_count
    if total_count == 0:
        count_stmt = select(func.count(Student.id)).where(and_(*category_filters))
        total_count = (await db.execute(count_stmt)).scalar() or 0

    def safe_isoformat(dt):
        if not dt: return None
        try: return dt.isoformat()
        except: return str(dt)

    return {
        "success": True,
        "total_count": total_count,
        "app_users_count": app_users_count,
        "data": [
            {
                "id": doc.id,
                "title": doc.title,
                "created_at": safe_isoformat(doc.created_at),
                "file_type": doc.file_type,
                "status": doc.status,
                "student": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "group_number": student.group_number,
                    "faculty_name": student.faculty_name
                }
            } for doc, student in rows
        ]
    }

@router.post("/documents/export-zip")
async def export_mgmt_documents_zip(
    query: str = None,
    faculty_id: int = None,
    title: str = None,
    education_type: str = None,
    education_form: str = None,
    level_name: str = None,
    specialty_name: str = None,
    group_number: str = None,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Download filtered documents, zip them and send to management user via Telegram.
    """
    from database.models import UserDocument
    from bot import bot
    from config import BOT_TOKEN
    from aiogram.types import BufferedInputFile
    
    # 1. Security Check
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) == 'rahbariyat'
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # 2. Build Query
    category_filters = [Student.university_id == uni_id]
    
    # Restrict by faculty if applicable
    if f_id:
        category_filters.append(Student.faculty_id == f_id)
    elif faculty_id:
        category_filters.append(Student.faculty_id == faculty_id)
    if education_type: category_filters.append(Student.education_type == education_type)
    if education_form: category_filters.append(Student.education_form == education_form)
    if level_name: category_filters.append(Student.level_name == level_name)
    if specialty_name: category_filters.append(Student.specialty_name == specialty_name)
    if group_number: category_filters.append(Student.group_number == group_number)

    stmt = (
        select(UserDocument, Student)
        .join(Student, UserDocument.student_id == Student.id)
        .where(and_(*category_filters))
    )

    if title:
        stmt = stmt.where(UserDocument.title == title)
        
    if query:
        stmt = stmt.where(
            (Student.full_name.ilike(f"%{query}%")) |
            (UserDocument.title.ilike(f"%{query}%"))
        )

    # Order by date
    stmt = stmt.order_by(UserDocument.created_at.desc())
    
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {"success": False, "message": "Hujjatlar topilmadi"}

    # 3. Create ZIP in memory
    zip_buffer = io.BytesIO()
    count = 0
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        async with aiohttp.ClientSession() as session:
            for doc, student in rows:
                try:
                    # Get File Info from Telegram
                    tg_file = await bot.get_file(doc.file_id)
                    file_path = tg_file.file_path
                    download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    
                    # Download File
                    async with session.get(download_url) as resp:
                        if resp.status == 200:
                            file_bytes = await resp.read()
                            
                            # Determine Extension
                            ext = "jpg"
                            if doc.file_type == "document":
                                if "." in file_path:
                                    ext = file_path.split(".")[-1]
                                else:
                                    ext = "bin"
                            
                            # Filename: StudentName_DocTitle_ID.ext
                            clean_name = student.full_name.replace(" ", "_").replace("'", "").replace('"', "")
                            clean_title = doc.title.replace(" ", "_").replace("'", "").replace('"', "")
                            filename = f"{clean_name}_{clean_title}_{doc.id}.{ext}"
                            
                            zip_file.writestr(filename, file_bytes)
                            count += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error zipping doc {doc.id}: {e}")

    if count == 0:
        return {"success": False, "message": "Hech qanday fayl yuklab olinmadi"}

    zip_buffer.seek(0)
    
    # 4. Send ZIP via Bot
    # Use TEST ID: 7476703866
    try:
        input_file = BufferedInputFile(zip_buffer.read(), filename="hujjatlar_arxivi.zip")
        caption = (
            f"📦 <b>Hujjatlar Arxivi (ZIP)</b>\n\n"
            f"Soni: <b>{count} ta</b>\n"
            f"Filtr: <b>{title or 'Barchasi'}</b>"
        )
        await bot.send_document(7476703866, input_file, caption=caption)
        return {"success": True, "message": f"ZIP fayl yuborildi ({count} ta hujjat). TEST ID: 7476703866"}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending ZIP: {e}")
        return {"success": False, "message": f"ZIP yuborishda xatolik yuz berdi: {str(e)}"}


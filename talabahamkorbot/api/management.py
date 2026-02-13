from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List, Optional
import zipfile
import io
import aiohttp
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import httpx

from api.dependencies import get_current_student, get_current_staff
from database.db_connect import get_db
from database.models import Student, Staff, TgAccount, UserActivity, TutorGroup
from database.models import StaffRole
from services.analytics_service import get_management_analytics
from services.ai_service import generate_answer_by_key
from data.ai_prompts import AI_PROMPTS
import json

# [NEW] Import Analytics Router
from api.analytics import router as analytics_router

router = APIRouter(prefix="/management", tags=["Management"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])



@router.get("/dashboard")
async def get_management_dashboard(
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get university-wide statistics for management dashboard.
    """
    # 1. Role Check (Explicit for Rahbariyat, Tyutor, Rector, Deans, and Prorektor)
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR]
    
    current_role = getattr(staff, 'role', None) or ""
    is_mgmt = (
        getattr(staff, 'hemis_role', None) == 'rahbariyat' or 
        current_role in global_mgmt_roles or 
        current_role in dean_level_roles or
        current_role == StaffRole.TYUTOR
    )
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat, dekanat yoki tyutorlar uchun")

    uni_id = getattr(staff, 'university_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    from services.hemis_service import HemisService
    
    token = getattr(staff, 'hemis_token', None)
    # 2. Filter by Faculty (Dean) or Group (Tutor) if restricted
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)
    
    # Priority: API -> DB (Fallback)
    # If Dean or Tutor, avoid API for now as it might return global counts
    if s_role == 'tyutor':
        # 1. Get Tutor groups
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        
        # [FIX] Use HEMIS API for Total Count (Admin Token for visibility)
        from config import HEMIS_ADMIN_TOKEN
        hemis_count = await HemisService.get_total_students_for_groups(group_numbers, HEMIS_ADMIN_TOKEN)
        
        if hemis_count > 0:
            total_students = hemis_count
        else:
            # Fallback to DB
            total_students = await db.scalar(
                select(func.count(Student.id)).where(Student.university_id == uni_id, Student.group_number.in_(group_numbers))
            ) or 0
            
        platform_users = await db.scalar(
            select(func.count(Student.id))
            .where(Student.university_id == uni_id, Student.group_number.in_(group_numbers), Student.hemis_token != None)
        ) or 0
        total_staff = 1 # Just the tutor themselves or 0 if counting others
        
    elif f_id:
        # Dean level
        from config import HEMIS_ADMIN_TOKEN
        if HEMIS_ADMIN_TOKEN:
             # [FIX] Map Local DB ID to correct HEMIS ID for Admin API filtering
             h_fac_id = f_id
             if f_id == 36: h_fac_id = 4 # Jurnalistika
             elif f_id == 34: h_fac_id = 2 # PR
             elif f_id == 42: h_fac_id = 35 # SIRTQI
             elif f_id == 37: h_fac_id = 16 # MAGISTRATURA
             
             # Use Admin API for accurate HEMIS count, but scope it to THIS faculty
             admin_filters = {"_department": h_fac_id}
             _, total_students = await HemisService.get_admin_student_list(admin_filters, limit=1)
        else:
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
        total_students_api = await HemisService.get_total_student_count(token)
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

# --- SHARED FILTER BUILDER ---
def build_student_filter(
    staff,
    faculty_id: int = None,
    education_type: str = None,
    education_form: str = None,
    level_name: str = None,
    specialty_name: str = None,
    group_number: str = None
):
    """
    Constructs a list of SQLAlchemy filters for Student queries.
    Enforces role-based scoping (Dean, Tutor) and dynamic dependencies.
    """
    uni_id = getattr(staff, 'university_id', None)
    staff_role = getattr(staff, 'role', None)
    
    global_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    is_global = getattr(staff, 'hemis_role', None) == 'rahbariyat' or staff_role in global_roles

    filters = []
    if uni_id:
        filters.append(Student.university_id == uni_id)
    elif not is_global:
        # If not global and no uni_id, they shouldn't see anything or it's an error
        # But we'll follow the existing requirement of throwing 400 in endpoints if needed
        filters.append(Student.university_id == -1) 
    
    # 1. Role-based Scoping
    staff_fac_id = getattr(staff, 'faculty_id', None)
    
    # Dean / Faculty Admin Scoping
    if not is_global and staff_fac_id and staff_role != 'tyutor':
        filters.append(Student.faculty_id == staff_fac_id)
        # Force faculty filter to match staff's faculty
        faculty_id = staff_fac_id

    # Tutor Scoping (Will be handled by group list usually, but here for safety)
    # We will handle Tutor group filtering dynamically in endpoints where needed
    # via the group_number filter, but we can't easily restrict the base query 
    # without joining TutorGroup, so we'll leave it to specific endpoints or 
    # rely on the fact that Tutors only see their groups in dropdowns.

    # 2. Dynamic Filters (Dependent)
    if faculty_id:
        filters.append(Student.faculty_id == faculty_id)
        
    if education_type:
        filters.append(Student.education_type.ilike(f"%{education_type}%"))
        
    if education_form:
        filters.append(Student.education_form.ilike(f"%{education_form}%"))
        
    if level_name:
        # Flexible matching
        filters.append(Student.level_name.ilike(f"%{level_name}%"))
        
    if specialty_name:
        filters.append(Student.specialty_name.ilike(f"%{specialty_name}%"))
        
    if group_number:
        filters.append(Student.group_number == group_number)
        
    if not filters:
        from sqlalchemy import true
        return [true()]
        
    return filters

@router.get("/faculties")
async def get_mgmt_faculties(
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get distinct faculties present in the Student database.
    Dynamically scoped by user role.
    """
    uni_id = getattr(staff, 'university_id', None)
    staff_role = getattr(staff, 'role', None)
    
    # 1. Access Check for Metadata
    global_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    is_global = getattr(staff, 'hemis_role', None) == 'rahbariyat' or staff_role in global_roles

    if not uni_id and not is_global:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    s_role = getattr(staff, 'role', None)
    
    # 1. Tutor Logic: Only show faculties where they have students
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        
        if not group_numbers:
            return {"success": True, "data": []}
            
        stmt = (
            select(Student.faculty_id, Student.faculty_name)
            .where(
                Student.university_id == uni_id, 
                Student.group_number.in_(group_numbers),
                Student.faculty_id != None
            )
            .distinct()
        )
    else:
        # 2. General Logic (with recursive scoping via helper principle)
        # We manually build it here because we select specific columns
        filters = build_student_filter(staff) # Base filters (Uni + Staff Faculty)
        stmt = (
            select(Student.faculty_id, Student.faculty_name)
            .where(
                *filters,
                Student.faculty_id != None,
                Student.faculty_name != None
            )
            .distinct()
            .order_by(Student.faculty_name)
        )

    result = await db.execute(stmt)
    faculties_data = result.all()
    
    return {
        "success": True, 
        "data": [{"id": f[0], "name": f[1]} for f in faculties_data]
    }

@router.get("/education-types")
async def get_mgmt_education_types(
    faculty_id: int = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available education types.
    Dependent on Faculty.
    """
    filters = build_student_filter(staff, faculty_id=faculty_id)
    
    # Tutor check for base filters
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    stmt = (
        select(Student.education_type)
        .where(
            *filters,
            Student.education_type != None
        )
        .distinct()
        .order_by(Student.education_type)
    )
    
    result = await db.execute(stmt)
    types = [r for r in result.scalars().all() if r]
    return {"success": True, "data": sorted(types)}

@router.get("/levels")
async def get_mgmt_levels(
    faculty_id: int = None,
    education_type: str = None,
    education_form: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available levels (Courses).
    Dependent on Faculty, Type, Form.
    """
    filters = build_student_filter(
        staff, 
        faculty_id=faculty_id,
        education_type=education_type,
        education_form=education_form
    )

    # Tutor check
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    stmt = (
        select(Student.level_name)
        .where(*filters)
        .distinct()
        .order_by(Student.level_name)
    )
    
    result = await db.execute(stmt)
    levels = [r for r in result.scalars().all() if r]
    
    # Sort natural (1, 2, 3...)
    def natural_sort_key(s):
        import re
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', s)]
    
    return {"success": True, "data": sorted(levels, key=natural_sort_key)}

@router.get("/education-forms")
async def get_mgmt_education_forms(
    faculty_id: int = None,
    education_type: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available education forms.
    Dependent on Faculty, Type.
    """
    filters = build_student_filter(
        staff, 
        faculty_id=faculty_id,
        education_type=education_type
    )
    
    # Tutor check
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    stmt = (
        select(Student.education_form)
        .where(*filters, Student.education_form != None)
        .distinct()
        .order_by(Student.education_form)
    )
    result = await db.execute(stmt)
    forms = [r for r in result.scalars().all() if r]
    return {"success": True, "data": sorted(forms)}


@router.get("/groups")
async def get_mgmt_groups_list(
    faculty_id: int = None,
    education_type: str = None,
    education_form: str = None,
    level_name: str = None,
    specialty_name: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available groups.
    Fully dependent on all other filters.
    """
    filters = build_student_filter(
        staff,
        faculty_id=faculty_id,
        education_type=education_type,
        education_form=education_form,
        level_name=level_name,
        specialty_name=specialty_name
    )
    
    # Tutor check
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    stmt = (
        select(Student.group_number)
        .where(*filters)
        .distinct()
        .order_by(Student.group_number)
    )
    result = await db.execute(stmt)
    groups = [r for r in result.scalars().all() if r]
    return {"success": True, "data": groups}


@router.get("/specialties")
async def get_mgmt_specialties(
    faculty_id: int = None,
    education_type: str = None,
    education_form: str = None,
    level_name: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available specialties.
    Dependent on Faculty, Type, Form, Level.
    """
    filters = build_student_filter(
        staff,
        faculty_id=faculty_id,
        education_type=education_type,
        education_form=education_form,
        level_name=level_name
    )
    
    # Tutor check
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    stmt = (
        select(Student.specialty_name)
        .where(*filters, Student.specialty_name != None)
        .distinct()
        .order_by(Student.specialty_name)
    )
    result = await db.execute(stmt)
    specialties = [r for r in result.scalars().all() if r]
    
    return {"success": True, "data": sorted(specialties)}

# Duplicate removed

@router.get("/groups/{group_number}/students")
async def get_mgmt_group_students(
    group_number: str,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    # Security
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)

    stmt = select(Student).where(Student.group_number == group_number, Student.university_id == uni_id)
    
    # Role-based restriction
    if s_role == 'tyutor':
        # Verify group belongs to tutor
        tg_stmt = select(TutorGroup).where(TutorGroup.tutor_id == staff.id, TutorGroup.group_number == group_number)
        tg_exists = (await db.execute(tg_stmt)).scalar_one_or_none()
        if not tg_exists:
            raise HTTPException(status_code=403, detail="Bu guruh sizga biriktirilmagan")
    elif f_id:
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
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    uni_id = getattr(staff, 'university_id', None)
    if uni_id is None:
        return {"success": True, "total_count": 0, "app_users_count": 0, "data": []}
    
    # [FIX] Normalize empty strings from frontend
    if education_type in ["", "All", "-1", "none"]: education_type = None
    if education_form in ["", "All", "-1", "none"]: education_form = None
    if level_name in ["", "All", "-1", "none"]: level_name = None
    if specialty_name in ["", "All", "-1", "none"]: specialty_name = None
    if group_number in ["", "All", "-1", "none"]: group_number = None

    # [FIX] Smart Filter Mapping (Frontend sends Form as Type sometimes)
    known_forms = ["Kunduzgi", "Kechki", "Sirtqi", "Masofaviy"]
    if education_type and education_type in known_forms:
        education_form = education_type
        education_type = None
    
    # 1. Build DB Filters First (Unified Logic)
    db_filters = build_student_filter(
        staff,
        faculty_id=faculty_id,
        education_type=education_type,
        education_form=education_form,
        level_name=level_name,
        specialty_name=specialty_name,
        group_number=group_number
    )
    
    search_filters = list(db_filters)
    if query:
        search_filters.append(
            (Student.full_name.ilike(f"%{query}%")) | 
            (Student.hemis_id.ilike(f"%{query}%")) |
            (Student.hemis_login.ilike(f"%{query}%"))
        )
        
    # 2. Get Stats & Data
    from services.hemis_service import HemisService
    from config import HEMIS_ADMIN_TOKEN
    
    # Logic: Prioritize DB for consistent filtering, but use HEMIS API if possible for fuller list
    total_count = 0
    students = []
    
    # Check if we should use Admin API (Only if simple filters, avoiding complex map logic)
    # The user requested "Take from DB", so we prioritize DB for filtering accuracy.
    # Admin API is hard to map perfectly dynamically without hardcoding IDs.
    # So we use DB for list, but maybe Admin API for total count if filters are empty?
    # Let's stick to DB as primary source per user request "Database ma'lumotiga asoslanib".
    
    # Count Query
    count_stmt = select(func.count(Student.id)).where(and_(*search_filters))
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    # Data Query
    stmt = select(Student).where(and_(*search_filters)).order_by(Student.full_name).limit(500)
    result = await db.execute(stmt)
    students = result.scalars().all()
    
    # App Users Count
    app_users_stmt = select(func.count(Student.id)).where(
        and_(*search_filters),
        Student.hemis_token != None
    )
    app_users_count = (await db.execute(app_users_stmt)).scalar() or 0

    # [NEW] Enrich with Activity Counts
    student_ids = [s.id for s in students if s.id]
    activity_counts = {}
    
    if student_ids:
        # Aggregate counts for these students
        count_stmt = (
            select(UserActivity.student_id, func.count(UserActivity.id))
            .where(UserActivity.student_id.in_(student_ids))
            .group_by(UserActivity.student_id)
        )
        count_res = await db.execute(count_stmt)
        activity_counts = {row[0]: row[1] for row in count_res.all()}
        
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
                "education_form": s.education_form,
                "activities_count": activity_counts.get(s.id, 0) # [NEW]
            } for s in students
        ]
    }

# Duplicate removed

@router.get("/staff/search")
async def search_mgmt_staff(
    query: str = None,
    faculty_id: int = None,
    role: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Search and filter university staff members with activity status.
    """
    # Security Check
    global_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR]
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in global_roles or getattr(staff, 'role', None) == StaffRole.TYUTOR
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat, tyutor yoki rektorat uchun")
        
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)
    
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # If restricted, force search within faculty (Dean)
    if s_role == 'rahbariyat' and f_id:
        faculty_id = f_id
        
    # If Tutor, restrict to assigned groups
    # Note: This endpoint returns faculties. For tutors, we still return the faculty list 
    # but maybe only their own faculty? 
    # Actually, tutors usually belong to one faculty.
    if s_role == 'tyutor' and f_id:
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
async def get_mgmt_groups_simple(
    faculty_id: int = None,
    education_type: str = None,
    education_form: str = None,
    specialty_name: str = None,
    level_name: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    from services.hemis_service import HemisService
    from config import HEMIS_ADMIN_TOKEN

    # [NEW] Scoping Logic for Deans
    s_role = getattr(staff, 'role', None) or ""
    f_id_restricted = getattr(staff, 'faculty_id', None)
    global_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    is_global = (
        getattr(staff, 'hemis_role', None) == 'rahbariyat' or 
        s_role in global_roles
    )
    
    # [NEW] Enforce Bakalavr for Deans
    if not is_global and f_id_restricted:
        education_type = "Bakalavr"

    effective_faculty_id = faculty_id
    if not is_global and f_id_restricted:
        effective_faculty_id = f_id_restricted
        
    # [FIX] Translate to HEMIS ID for Admin API
    h_fac_id = effective_faculty_id
    if effective_faculty_id == 36: h_fac_id = 4 # Jurnalistika
    elif effective_faculty_id == 34: h_fac_id = 2 # PR
    elif effective_faculty_id == 42: h_fac_id = 35 # SIRTQI
    elif effective_faculty_id == 37: h_fac_id = 16 # MAGISTRATURA
    
    # [FIX] Translate to DB ID for DB Query
    db_fac_id = effective_faculty_id
    if effective_faculty_id == 4: db_fac_id = 36
    elif effective_faculty_id == 2: db_fac_id = 34
    elif effective_faculty_id == 35: db_fac_id = 42
    elif effective_faculty_id == 16: db_fac_id = 37
    
    # [FIX] Smart Normalize empty strings for group search
    if education_type in ["", "All", "-1", "none"]: education_type = None
    if education_form in ["", "All", "-1", "none"]: education_form = None
    if specialty_name in ["", "All", "-1", "none"]: specialty_name = None
    if level_name in ["", "All", "-1", "none"]: level_name = None

    # 1. Try Admin API (University-wide)
    if HEMIS_ADMIN_TOKEN:
        if s_role == 'tyutor':
            # Fallback to local DB for Tutors
            pass 
        else:
            spec_id = None
            if specialty_name:
                spec_id = await HemisService.resolve_specialty_id(
                    specialty_name, 
                    education_type,
                    faculty_id=h_fac_id, # Use translated ID
                    education_form=education_form
                )
    
            all_groups = await HemisService.get_group_list(
                faculty_id=h_fac_id, # Use translated ID
                specialty_id=spec_id,
                education_type=education_type,
                education_form=education_form,
                level_name=level_name
            )
            if all_groups:
                 group_names = [g.get("name") for g in all_groups if g.get("name")]
                 return {"success": True, "data": sorted(list(set(group_names)))}

    # 2. Fallback to Local DB
    uni_id = getattr(staff, 'university_id', None)
    stmt = select(Student.group_number).where(
        Student.university_id == uni_id, 
        Student.group_number != None
    )
    
    if s_role == 'tyutor':
        from database.models import TutorGroup
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        stmt = stmt.where(Student.group_number.in_(group_numbers))
        
    if db_fac_id:
        stmt = stmt.where(Student.faculty_id == db_fac_id)
    if education_type:
        stmt = stmt.where(Student.education_type.ilike(f"%{education_type}%"))
    if education_form:
        stmt = stmt.where(Student.education_form.ilike(f"%{education_form}%"))
    if level_name:
        # Standardize for DB
        lvl_db = level_name
        if "-kurs" not in level_name.lower(): lvl_db = f"{level_name}-kurs"
        stmt = stmt.where(Student.level_name.ilike(lvl_db))
    if specialty_name:
        stmt = stmt.where(Student.specialty_name == specialty_name)
        
    result = await db.execute(stmt.distinct().order_by(Student.group_number))
    groups = result.scalars().all()
    
    return {"success": True, "data": groups}

@router.get("/students/{student_id}/full-details")
async def get_mgmt_student_details(
    student_id: int,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    try:
        from database.models import UserActivity, StudentDocument, StudentFeedback
        
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

        # 3. Documents (Unified Table)
        all_docs_result = await db.execute(
            select(StudentDocument)
            .where(StudentDocument.student_id == student_id)
            .order_by(StudentDocument.uploaded_at.desc())
        )
        all_docs = all_docs_result.scalars().all()
        
        docs = [d for d in all_docs if d.file_type == "document"]
        certs = [d for d in all_docs if d.file_type == "certificate"]

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
                    "gpa": getattr(student, 'gpa', 0.0),
                    # [NEW] Enhanced Fields
                    "education_type": getattr(student, 'education_type', None),
                    "specialty_name": getattr(student, 'specialty_name', None),
                    "level_name": getattr(student, 'level_name', None),
                    "education_form": getattr(student, 'education_form', None),
                    "is_app_user": bool(getattr(student, 'hemis_token', None)),
                    "last_active": student.last_login.isoformat() if getattr(student, 'last_login', None) else None
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
                        "title": d.file_name, 
                        "created_at": safe_isoformat(d.uploaded_at)
                    } for d in docs
                ],
                "certificates": [
                    {
                        "id": c.id, 
                        "title": c.file_name, 
                        "created_at": safe_isoformat(c.uploaded_at)
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
    staff: Any = Depends(get_current_staff),
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
    staff: Any = Depends(get_current_staff),
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
    staff: Any = Depends(get_current_staff),
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
    
    # 1. Get Document and Student Info
    stmt = (
        select(StudentDocument, Student)
        .join(Student, StudentDocument.student_id == Student.id)
        .where(StudentDocument.id == cert_id)
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
    tg_acc = await db.scalar(select(TgAccount).where(
        (TgAccount.student_id == staff.id) | (TgAccount.staff_id == staff.id)
    ))
    
    if not tg_acc:
        return {"success": False, "message": "Sizning Telegram hisobingiz ulanmagan. Iltimos, botga kiring."}

    # 4. Send via Bot
    try:
        caption = (
            f"🎓 <b>Talaba Sertifikati (Rahbariyat)</b>\n\n"
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
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending cert to management: {e}")
        return {"success": False, "message": f"Botda xatolik yuz berdi: {str(e)}"}

@router.post("/documents/{doc_id}/download")
async def send_student_doc_to_management(
    doc_id: int,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends the document file to the management user's Telegram bot.
    """
    # 1. Get Document and Student Info
    stmt = (
        select(StudentDocument, Student)
        .join(Student, StudentDocument.student_id == Student.id)
        .where(StudentDocument.id == doc_id)
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
            f"Hujjat: <b>{doc.file_name}</b>"
        )
        
        # Better detection
        is_photo = doc.mime_type and "image" in doc.mime_type
        
        if is_photo:
            await bot.send_photo(tg_acc.telegram_id, doc.telegram_file_id, caption=caption, parse_mode="HTML")
        else:
            await bot.send_document(tg_acc.telegram_id, doc.telegram_file_id, caption=caption, parse_mode="HTML")
            
        return {"success": True, "message": "Hujjat botga yuborildi"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Error sending doc: {e}")
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending doc to management: {e}")
        return {"success": False, "message": f"Botda xatolik yuz berdi: {str(e)}"}
@router.get("/documents/{doc_id}/download")
async def download_student_document(
    doc_id: int,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a student document by streaming it from Telegram Cloud.
    """
    from database.models import StudentDocument
    from config import BOT_TOKEN
    from bot import bot

    # 1. Security Check
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    
    staff_role = getattr(staff, 'role', None) or getattr(staff, 'hemis_role', None)
    is_mgmt = staff_role == 'rahbariyat' or staff_role in global_mgmt_roles or staff_role == StaffRole.TYUTOR or staff_role in dean_level_roles
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    # 2. Get Document
    doc = await db.get(StudentDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")

    # [OPTIONAL] Scoping check: Ensure Dean only downloads from their faculty
    if staff_role in dean_level_roles:
        # Check student faculty
        from database.models import Student
        student = await db.get(Student, doc.student_id)
        if not student or student.faculty_id != staff.faculty_id:
             raise HTTPException(status_code=403, detail="Sizga ushbu hujjatni ko'rishga ruxsat yo'q")

    # 3. Fetch from Telegram
    try:
        file = await bot.get_file(doc.telegram_file_id)
        file_path = file.file_path
        url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        async def iterate_file():
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk

        # Sanitize filename
        safe_filename = doc.file_name.replace(" ", "_").replace("/", "_")
        if "." not in safe_filename:
            # Try to guess extension from mime_type or path
            ext = file_path.split(".")[-1] if "." in file_path else "bin"
            safe_filename += f".{ext}"

        return StreamingResponse(
            iterate_file(),
            media_type=doc.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Telegramdan faylni yuklab olishda xatolik: {str(e)}")

@router.get("/archive")
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
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all student documents for management with filtering.
    """
    from database.models import StudentDocument
    
    # 1. Security & Role Resolution
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    
    staff_role = getattr(staff, 'role', None) or getattr(staff, 'hemis_role', None)
    is_mgmt = staff_role == 'rahbariyat' or staff_role in global_mgmt_roles or staff_role == StaffRole.TYUTOR or staff_role in dean_level_roles
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    # 2. Build Base Filters
    category_filters = build_student_filter(
        staff, faculty_id, education_type, education_form, level_name, specialty_name, group_number
    )
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"ARCHIVE_REQ: Staff: {staff.id}, Role: {staff_role}, Filters: {category_filters}, Title: {title}")

    # 3. Construction of Query
    stmt = select(StudentDocument).join(Student).where(and_(*category_filters)).options(selectinload(StudentDocument.student))
    
    if query:
        stmt = stmt.where(
            (StudentDocument.file_name.ilike(f"%{query}%")) | 
            (Student.full_name.ilike(f"%{query}%"))
        )
        
    if title and title != "Hammasi":
        if title == "Sertifikatlar":
            stmt = stmt.where(StudentDocument.file_type == "certificate")
        elif title == "Hujjatlar":
            stmt = stmt.where(StudentDocument.file_type == "document")
        else:
            stmt = stmt.where(StudentDocument.file_name.ilike(f"%{title}%"))

    # 4. Pagination & Fetch
    # Get total count first
    total_count = await db.scalar(
        select(func.count(StudentDocument.id))
        .join(Student)
        .where(
            and_(
                *category_filters,
                (StudentDocument.file_name.ilike(f"%{query}%") if query else True),
                ((StudentDocument.file_type == "certificate" if title == "Sertifikatlar" else (StudentDocument.file_type == "document" if title == "Hujjatlar" else StudentDocument.file_name.ilike(f"%{title}%"))) if title and title != "Hammasi" else True)
            )
        )
    )

    res = await db.execute(
        stmt.order_by(StudentDocument.uploaded_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    docs = res.scalars().all()

    data = []
    for d in docs:
        data.append({
            "id": str(d.id),
            "title": d.file_name,
            "created_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            "file_id": d.telegram_file_id,
            "file_type": d.file_type or "document",
            "is_certificate": d.file_type == "certificate",
            "student": {
                "full_name": d.student.full_name if d.student else "Noma'lum",
                "group_number": d.student.group_number if d.student else "",
                "faculty_name": d.student.faculty_name if d.student else "",
            }
        })

    # [NEW] Simple Stats
    stats = {
        "total_documents": await db.scalar(select(func.count(StudentDocument.id)).where(and_(*category_filters, StudentDocument.file_type == "document"))),
        "total_certificates": await db.scalar(select(func.count(StudentDocument.id)).where(and_(*category_filters, StudentDocument.file_type == "certificate")))
    }
    
    return {
        "success": True, 
        "data": data, 
        "total_count": total_count or 0,
        "stats": stats
    }

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
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Download filtered documents, zip them and send to management user via Telegram.
    """
    from database.models import StudentDocument
    from bot import bot
    from config import BOT_TOKEN
    from aiogram.types import BufferedInputFile
    
    # 1. Security Check
    dean_level_roles = [StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.DEKANAT]
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR, StaffRole.OWNER, StaffRole.DEVELOPER]
    
    staff_role = getattr(staff, 'role', None) or getattr(staff, 'hemis_role', None)
    is_mgmt = staff_role == 'rahbariyat' or staff_role in global_mgmt_roles or staff_role in dean_level_roles
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")

    # 2. Build Query Filters
    category_filters = build_student_filter(
        staff, faculty_id, education_type, education_form, level_name, specialty_name, group_number
    )
    
    # [NEW] Collect all results to ZIP
    all_docs_to_export = []

    # 3. Fetch Documents from Unified Table
    stmt = (
        select(StudentDocument)
        .join(Student, StudentDocument.student_id == Student.id)
        .where(and_(*category_filters))
    )
    
    if query:
        stmt = stmt.where(
            (StudentDocument.file_name.ilike(f"%{query}%")) |
            (Student.full_name.ilike(f"%{query}%"))
        )
    
    if title and title != "Hammasi":
        if title == "Sertifikatlar":
            stmt = stmt.where(StudentDocument.file_type == "certificate")
        else:
            stmt = stmt.where(StudentDocument.file_name.ilike(f"%{title}%"))
            
    res = await db.execute(stmt.options(selectinload(StudentDocument.student)))
    all_docs_to_export = res.scalars().all()

    # 5. Process and ZIP
    if not all_docs_to_export:
        return {"success": False, "message": "Hech qanday hujjat topilmadi"}

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    count = 0
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        async with aiohttp.ClientSession() as session:
            for doc in all_docs_to_export:
                student = doc.student
                if not student: continue
                
                try:
                    # Get File Info from Telegram
                    tg_file = await bot.get_file(doc.telegram_file_id)
                    file_path = tg_file.file_path
                    download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                    
                    # Download File
                    async with session.get(download_url) as resp:
                        if resp.status == 200:
                            file_bytes = await resp.read()
                            
                            # Determine Extension
                            ext = file_path.split(".")[-1] if "." in file_path else "bin"
                            
                            # Filename: StudentName_DocTitle_ID.ext
                            clean_name = student.full_name.replace(" ", "_").replace("'", "").replace("\"", "")
                            clean_title = doc.file_name.replace(" ", "_").replace("'", "").replace("\"", "")
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
    
    # Send ZIP via Bot
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


# ============================================================
# SOCIAL ACTIVITY MODERATION [NEW]
# ============================================================

class ActivityModerationRequest(BaseModel):
    comment: Optional[str] = None

@router.get("/activities")
async def get_management_activities(
    status: Optional[str] = None,
    category: Optional[str] = None,
    faculty_id: Optional[int] = None,
    query: Optional[str] = None,
    education_type: Optional[str] = None,
    education_form: Optional[str] = None,
    level_name: Optional[str] = None,
    specialty_name: Optional[str] = None,
    group_number: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    List and filter student activities for management.
    """
    # Security Check
    role = str(getattr(staff, 'role', None)).lower()
    allowed_roles = ['rahbariyat', 'dekanat', 'tyutor', 'rektor', 'prorektor', 'owner', 'developer', 'yoshlar_yetakchisi', 'yoshlar_ittifoqi']
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or role in allowed_roles
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    role = str(getattr(staff, 'role', None)).lower()
    
    stmt = (
        select(UserActivity)
        .join(Student, UserActivity.student_id == Student.id)
        .options(selectinload(UserActivity.student), selectinload(UserActivity.images))
    )

    # 1. University Scoping
    global_roles = ['owner', 'developer', 'rahbariyat', 'rektor', 'prorektor', 'yoshlar_yetakchisi', 'yoshlar_ittifoqi']
    if uni_id:
        stmt = stmt.where(Student.university_id == uni_id)
    elif role not in global_roles:
        # Restricted role but no uni_id -> no results for safety
        return {"success": True, "total": 0, "page": page, "limit": limit, "data": []}

    # 2. Faculty Scoping (Explicit filter takes precedence)
    if faculty_id:
        stmt = stmt.where(Student.faculty_id == faculty_id)
    elif f_id and role not in ['rahbariyat', 'owner', 'developer', 'rektor', 'prorektor', 'yoshlar_yetakchisi']:
        # Dekanat/Tyutor restriction
        stmt = stmt.where(Student.faculty_id == f_id)
        # [NEW] Enforce Bakalavr Only for Deans
        dean_and_tutor_roles = ['dekan', 'dekan_orinbosari', 'dekan_yoshlar', 'dekanat', 'tyutor']
        if role in dean_and_tutor_roles:
             stmt = stmt.where(Student.education_type.ilike("Bakalavr"))

    if status:
        stmt = stmt.where(UserActivity.status == status)
    if category:
        stmt = stmt.where(UserActivity.category == category)
    if query:
        stmt = stmt.where(
            (Student.full_name.ilike(f"%{query}%")) |
            (UserActivity.name.ilike(f"%{query}%")) |
            (Student.hemis_login.ilike(f"%{query}%"))
        )

    if education_type:
        stmt = stmt.where(Student.education_type.ilike(education_type))
    if education_form:
        stmt = stmt.where(Student.education_form.ilike(education_form))
    if level_name:
        stmt = stmt.where(Student.level_name.ilike(level_name))
    if specialty_name:
        stmt = stmt.where(Student.specialty_name.ilike(specialty_name))
    if group_number:
        stmt = stmt.where(Student.group_number.ilike(group_number))

    # Pagination count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = await db.scalar(count_stmt) or 0

    stmt = stmt.order_by(desc(UserActivity.created_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    activities = result.scalars().all()

    return {
        "success": True,
        "total": total_count,
        "page": page,
        "limit": limit,
        "data": [
            {
                "id": a.id,
                "student_id": a.student_id,
                "student_full_name": a.student.full_name,
                "faculty_name": a.student.faculty_name,
                "category": a.category,
                "name": a.name,
                "description": a.description,
                "date": a.date,
                "status": a.status,
                "moderator_comment": a.moderator_comment,
                "created_at": a.created_at,
                "images": [f"https://tengdosh.uzjoku.uz/api/v1/files?file_id={img.file_id}" for img in a.images]
            } for a in activities
        ]
    }

@router.post("/activities/{activity_id}/approve")
async def approve_mgmt_activity(
    activity_id: int,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a student activity.
    """
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or str(getattr(staff, 'role', None)).lower() in ['rahbariyat', 'dekanat', 'tyutor', 'rektor', 'prorektor', 'owner', 'developer']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    stmt = select(UserActivity).where(UserActivity.id == activity_id)
    activity = (await db.execute(stmt)).scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Faollik topilmadi")
    
    activity.status = "confirmed"
    await db.commit()
    return {"success": True, "message": "Faollik tasdiqlandi"}

@router.post("/activities/{activity_id}/reject")
async def reject_mgmt_activity(
    activity_id: int,
    req: ActivityModerationRequest,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a student activity with comment.
    """
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or str(getattr(staff, 'role', None)).lower() in ['rahbariyat', 'dekanat', 'tyutor', 'rektor', 'prorektor', 'owner', 'developer']
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Ruxsat etilmagan")

    stmt = select(UserActivity).where(UserActivity.id == activity_id)
    activity = (await db.execute(stmt)).scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Faollik topilmadi")
    
    activity.status = "rejected"
    activity.moderator_comment = req.comment
    await db.commit()
    return {"success": True, "message": "Faollik rad etildi"}


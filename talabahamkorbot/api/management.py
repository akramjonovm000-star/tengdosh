from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List, Optional
import zipfile
import io
import aiohttp
from pydantic import BaseModel

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
    # 1. Role Check (Explicit for Rahbariyat, Tyutor, Rector, and Prorektor)
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR]
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in global_mgmt_roles or getattr(staff, 'role', None) == StaffRole.TYUTOR
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat, tyutor yoki rektorat uchun")

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

@router.get("/faculties")
async def get_mgmt_faculties(
    staff: Any = Depends(get_current_staff),
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
    s_role = getattr(staff, 'role', None)

    # [NEW] Tutor Restriction: Only show faculties of assigned groups
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        
        if group_numbers:
            # Get faculties from students in these groups
            stmt = (
                select(Student.faculty_id, Student.faculty_name)
                .where(Student.university_id == uni_id, Student.group_number.in_(group_numbers))
                .distinct()
            )
            result = await db.execute(stmt)
            faculties_data = result.all()
            return {
                "success": True, 
                "data": [{"id": f[0], "name": f[1]} for f in faculties_data if f[0] and f[1]]
            }
        return {"success": True, "data": []}
    
    if HEMIS_ADMIN_TOKEN:
        faculties = await HemisService.get_faculties()
        if faculties:
             # Filter only specific faculties for this University structure
             allowed_ids = [4, 2, 43]
             filtered = [f for f in faculties if f['id'] in allowed_ids]
             
             if f_id:
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
    education_type: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    # Security: Ensure faculty belongs to staff's university
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)
    
    if f_id and f_id != faculty_id:
        raise HTTPException(status_code=403, detail="Sizga boshqa fakultet ma'lumotlari ruxsat berilmagan")
    
    # Base filter
    filters = [Student.faculty_id == faculty_id, Student.university_id == uni_id]
    
    # [NEW] Cascaded Filter: Type
    if education_type:
        filters.append(Student.education_type.ilike(f"%{education_type}%"))
    
    # Tutor specific filter
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    # Unique levels for this faculty
    result = await db.execute(
        select(Student.level_name)
        .where(*filters)
        .distinct()
        .order_by(Student.level_name)
    )
    levels = [r for r in result.scalars().all() if r]
    return {"success": True, "data": levels}

@router.get("/faculties/{faculty_id}/levels/{level_name}/groups")
async def get_mgmt_groups(
    faculty_id: int,
    level_name: str,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    # Security
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)
    
    if f_id and f_id != faculty_id:
        raise HTTPException(status_code=403, detail="Sizga boshqa fakultet ma'lumotlari ruxsat berilmagan")

    # Base filter
    filters = [
        Student.faculty_id == faculty_id, 
        Student.level_name == level_name,
        Student.university_id == uni_id
    ]
    
    # Tutor specific filter
    if str(s_role) == 'tyutor' or s_role == StaffRole.TYUTOR:
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))

    # Unique groups for this faculty and level
    result = await db.execute(
        select(Student.group_number)
        .where(*filters)
        .distinct()
        .order_by(Student.group_number)
    )
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
    from services.hemis_service import HemisService
    from config import HEMIS_ADMIN_TOKEN
    
    # 1. Try Admin API (University-wide)
    if HEMIS_ADMIN_TOKEN:
        # [NEW] Check Tutor Restriction first
        s_role = getattr(staff, 'role', None)
        if s_role == 'tyutor':
             # Fallback to Local DB logic for Tutors to ensure strict filtering by Group
             pass
        else:
            # [FIX] Cascaded Filtering: If Form or Level provided, use Group List to find valid Specialties
            if education_form or level_name:
                 groups = await HemisService.get_group_list(
                     faculty_id=faculty_id,
                     education_type=education_type,
                     education_form=education_form,
                     level_name=level_name
                 )
                 if groups:
                     # Extract unique specialties from groups
                     seen_ids = set()
                     specs = []
                     for g in groups:
                         s = g.get("specialty", {})
                         if s and s.get("name") and s.get("id") not in seen_ids:
                             seen_ids.add(s.get("id"))
                             specs.append(s.get("name"))
                     return {"success": True, "data": sorted(specs)}

            # Default fallback to Specialty List if no deep filters
            all_specs = await HemisService.get_specialty_list(faculty_id=faculty_id, education_type=education_type)
            if all_specs:
                return {"success": True, "data": sorted(list(set([s.get("name") for s in all_specs if s.get("name")])))}

    # 2. Fallback to Local DB
    uni_id = getattr(staff, 'university_id', None)
    stmt = select(Student.specialty_name).where(
        Student.university_id == uni_id, 
        Student.specialty_name != None
    )
    
    # [NEW] Tutor Filter
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        stmt = stmt.where(Student.group_number.in_(group_numbers))
        
    if faculty_id:
        stmt = stmt.where(Student.faculty_id == faculty_id)
    if education_type:
        stmt = stmt.where(Student.education_type == education_type)
    if education_form:
        stmt = stmt.where(Student.education_form == education_form)
    if level_name:
        stmt = stmt.where(Student.level_name == level_name)
        
    result = await db.execute(stmt.distinct().order_by(Student.specialty_name))
    specialties = result.scalars().all()
    
    return {"success": True, "data": specialties}

@router.get("/faculties/{faculty_id}/levels/{level_name}/groups")
async def get_mgmt_groups(
    faculty_id: int,
    level_name: str,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    # Security
    uni_id = getattr(staff, 'university_id', None)
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)
    
    if f_id and f_id != faculty_id:
        raise HTTPException(status_code=403, detail="Sizga boshqa fakultet ma'lumotlari ruxsat berilmagan")

    with open("mgmt_debug.log", "a") as f:
        f.write(f"DEBUG: get_mgmt_groups - staff_id: {getattr(staff, 'id', 'N/A')}, role: {s_role}, type: {type(s_role)}\n")

    # Base filter
    filters = [
        Student.faculty_id == faculty_id, 
        Student.level_name == level_name,
        Student.university_id == uni_id
    ]
    
    # Tutor specific filter
    if str(s_role) == 'tyutor' or s_role == StaffRole.TYUTOR:
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        with open("mgmt_debug.log", "a") as f:
            f.write(f"DEBUG: Found {len(group_numbers)} groups for tutor {staff.id}\n")
        filters.append(Student.group_number.in_(group_numbers))

    # Unique groups for this faculty and level
    result = await db.execute(
        select(Student.group_number)
        .where(*filters)
        .distinct()
        .order_by(Student.group_number)
    )
    groups = [r for r in result.scalars().all() if r]
    return {"success": True, "data": groups}

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
    
    # [FIX] Smart Filter Mapping (Frontend sends Form as Type)
    # Corrects "Turi" dropdown sending "Kunduzgi", "Sirtqi" etc.
    known_forms = ["Kunduzgi", "Kechki", "Sirtqi", "Masofaviy"]
    if education_type and education_type in known_forms:
        education_form = education_type
        education_type = None
    
    # 1. Base category filters (University + Dropdowns)
    category_filters = [Student.university_id == uni_id]
    # Custom Faculty ID Mapping for Local DB (Admin to Local)
    db_faculty_id = faculty_id
    if faculty_id == 4: db_faculty_id = 36   # Jurnalistika
    elif faculty_id == 2: db_faculty_id = 34 # PR
    elif faculty_id == 43: db_faculty_id = 35 # Xalqaro
    
    if db_faculty_id: category_filters.append(Student.faculty_id == db_faculty_id)
    if education_type: category_filters.append(Student.education_type.ilike(f"%{education_type}%"))
    if education_form: category_filters.append(Student.education_form.ilike(f"%{education_form}%"))
    if level_name: category_filters.append(Student.level_name == level_name)
    if specialty_name: category_filters.append(Student.specialty_name == specialty_name)
    if group_number: category_filters.append(Student.group_number == group_number)

    # 1a. Tutor and Dean specific restrictions
    s_role = getattr(staff, 'role', None)
    f_id = getattr(staff, 'faculty_id', None)
    
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        tg_res = await db.execute(tg_stmt)
        allowed_groups = tg_res.scalars().all()
        category_filters.append(Student.group_number.in_(allowed_groups))
    elif f_id:
        # Deans are restricted to their faculty
        category_filters.append(Student.faculty_id == f_id)

    # 2. Search filters (Dropdowns + Query)
    search_filters = list(category_filters)
    if query:
        search_filters.append(
            (Student.full_name.ilike(f"%{query}%")) | 
            (Student.hemis_id.ilike(f"%{query}%")) |
            (Student.hemis_login.ilike(f"%{query}%"))
        )


    
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
            # Standard Education Type mapping
            if "Bakalavr" in education_type:
                admin_filters["_education_type"] = 11
            elif "Magistr" in education_type:
                admin_filters["_education_type"] = 12
            
        # [FIX] Admin API Filter Mappings for Forms (Verified IDs)
        if education_form and not start_dept_override:
            if "Kunduzgi" in education_form:
                 admin_filters["_education_form"] = 11
            elif "Kechki" in education_form:
                 admin_filters["_education_form"] = 12
            elif "Sirtqi" in education_form:
                 admin_filters["_education_form"] = 13
            elif "Masofaviy" in education_form:
                 admin_filters["_education_form"] = 16
            
        if level_name:
            # Verified Level IDs: 1-kurs=11, 2-kurs=12, 3-kurs=13, 4-kurs=14
            if "1" in level_name: admin_filters["_level"] = 11
            elif "2" in level_name: admin_filters["_level"] = 12
            elif "3" in level_name: admin_filters["_level"] = 13
            elif "4" in level_name: admin_filters["_level"] = 14


        if specialty_name:
            # [FIX] Smart Resolution: Use Faculty and Form to find the correct specialty ID
            spec_id = await HemisService.resolve_specialty_id(
                specialty_name, 
                education_type, 
                faculty_id=faculty_id,
                education_form=education_form
            )
            if spec_id:
                admin_filters["_specialty"] = spec_id
            else:
                # If filter provided but not resolved, return empty to avoid false positives
                return {"success": True, "total_count": 0, "app_users_count": 0, "data": []}
                
        if group_number:
            grp_id = await HemisService.resolve_group_id(group_number)
            if grp_id:
                admin_filters["_group"] = grp_id
            else:
                # If filter provided but not resolved, return empty
                return {"success": True, "total_count": 0, "app_users_count": 0, "data": []}
        
        # [NEW] Handle Search Query (Name or ID)
        if query:
            # The 'search' param is reliable for names. 
            # Substring search for IDs often defaults to name search or is not supported.
            admin_filters["search"] = query
        
        # Fetch from Admin API (List + Count)
        
        admin_items, total_count = await HemisService.get_admin_student_list(
            admin_filters, page=1, limit=500
        )
        
        # [NEW] Tutor Filter Logic in Admin API Path
        # If user is Tutor, we must filter the results (items and count) to only their allowed groups
        s_role = getattr(staff, 'role', None)
        tutor_groups = []
        if s_role == 'tyutor':
             tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
             tutor_groups = (await db.execute(tg_stmt)).scalars().all()
             
        students = []
        filtered_admin_items = []

        # [NEW] Enhanced Tutor Fetching Strategy
        if s_role == 'tyutor' and tutor_groups:
             # Fetch ONLY the tutor's groups from API (Parallel Requests)
             # This guarantees accurate counts (e.g. 196) vs Local DB (91)
             admin_items, total_count = await HemisService.get_students_for_groups(tutor_groups, HEMIS_ADMIN_TOKEN)
             
             # Apply Search Query in Memory (since we fetched full group lists)
             if query:
                 q = query.lower()
                 admin_items = [
                     i for i in admin_items 
                     if q in (i.get("full_name") or "").lower() 
                     or q in (i.get("student_id_number") or "").lower()
                     or q in str(i.get("id"))
                 ]
                 total_count = len(admin_items)
                 
        else:
            # Standard Admin API Fetch (Dean / Rector)
            admin_items, total_count = await HemisService.get_admin_student_list(
                admin_filters, page=1, limit=500
            )
        
        if total_count > 0:
            # [NEW] Map Admin API Results to Local Database IDs (Optimization for Full Details)
            # Use student_id_number as the matching key for Students
            logins = [item.get("student_id_number") for item in admin_items if item.get("student_id_number")]
            login_to_id = {}
            if logins:
                l_stmt = select(Student.id, Student.hemis_login).where(Student.hemis_login.in_(logins))
                l_res = await db.execute(l_stmt)
                login_to_id = {row[1]: row[0] for row in l_res.all()}

            for item in admin_items:
                s = Student()
                login = item.get("student_id_number")
                # Use local ID (PK) if student has logged into app, else keep HEMIS ID for read-only display
                s.id = login_to_id.get(login, item.get("id")) 
                s.hemis_id = item.get("id")
                s.hemis_login = login
                s.full_name = item.get("full_name") or f"{item.get('second_name', '')} {item.get('first_name', '')} {item.get('third_name', '')}".strip()
                s.image_url = item.get("image")
                dept = item.get("department", {})
                s.faculty_name = dept.get("name") if isinstance(dept, dict) else ""
                grp = item.get("group", {})
                s.group_number = grp.get("name") if isinstance(grp, dict) else ""
                lvl = item.get("level", {})
                s.level_name = lvl.get("name") if isinstance(lvl, dict) else ""
                ef = item.get("educationForm", {})
                s.education_form = ef.get("name") if isinstance(ef, dict) else ""
                et = item.get("educationType", {})
                s.education_type = et.get("name") if isinstance(et, dict) else ""
                students.append(s)
        
        # If Admin API fails (cnt=0) and we have no filters, it might be an error or just empty.
        # If it returns 0 but DB has users, we might want to fallback to DB count?
        # But valid answer could be 0 (e.g. empty group).
        # Let's trust Admin API if it returns success (handled in service), but if 0, maybe check DB?
        # The service returns 0 on error.
        
        if total_count == 0 and s_role != 'tyutor': # Only fallback for non-tutors (tutors use strict filter above)
             # Fallback to DB if API failed or returned 0 (e.g. invalid filter ID or Short ID)
             # [FIX] Use search_filters for count, not just category_filters. 
             # search_filters includes the name/ID query logic.
             count_stmt = select(func.count(Student.id)).where(and_(*search_filters))
             db_count = (await db.execute(count_stmt)).scalar() or 0
             total_count = db_count
             
             # Fallback List (When Admin API returns 0)
             stmt = select(Student).where(and_(*search_filters)).order_by(Student.full_name).limit(500)
             result = await db.execute(stmt)
             students = result.scalars().all()
        
        # Fallback for Tutors if API returned 0 (and filtered list is empty)
        if total_count == 0 and s_role == 'tyutor':
             count_stmt = select(func.count(Student.id)).where(and_(*search_filters))
             total_count = (await db.execute(count_stmt)).scalar() or 0
             
             stmt = select(Student).where(and_(*search_filters)).order_by(Student.full_name).limit(500)
             result = await db.execute(stmt)
             students = result.scalars().all()

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
        
        # Execute Local Query for list (FALLBACK PATH ONLY)
        stmt = select(Student).where(and_(*search_filters)).order_by(Student.full_name).limit(500)
        result = await db.execute(stmt)
        students = result.scalars().all()

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

@router.get("/specialties")
async def get_mgmt_specialties(
    faculty_id: int = None,
    education_type: str = None,
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    from services.hemis_service import HemisService
    from config import HEMIS_ADMIN_TOKEN
    
    # 1. Try Admin API (University-wide)
    # [NEW] Check Tutor Role
    if HEMIS_ADMIN_TOKEN:
        s_role = getattr(staff, 'role', None) 
        if s_role == 'tyutor':
            pass # Fallback to DB
        else:
            all_specs = await HemisService.get_specialty_list(faculty_id=faculty_id, education_type=education_type)
            if all_specs:
                return {"success": True, "data": sorted(list(set([s.get("name") for s in all_specs if s.get("name")])))}

    # 2. Fallback to Local DB
    uni_id = getattr(staff, 'university_id', None)
    stmt = select(Student.specialty_name).where(
        Student.university_id == uni_id, 
        Student.specialty_name != None
    )
    
    # [NEW] Tutor Filter
    s_role = getattr(staff, 'role', None)
    if s_role == 'tyutor':
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        stmt = stmt.where(Student.group_number.in_(group_numbers))

    if faculty_id:
        stmt = stmt.where(Student.faculty_id == faculty_id)
    if education_type:
        stmt = stmt.where(Student.education_type == education_type)
        
    result = await db.execute(stmt.distinct().order_by(Student.specialty_name))
    specialties = result.scalars().all()
    
    return {"success": True, "data": specialties}

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

    # 1. Try Admin API (University-wide)
    if HEMIS_ADMIN_TOKEN:
        # Check Tutor Role
        s_role = getattr(staff, 'role', None)
        tutor_groups = []
        if s_role == 'tyutor':
            from database.models import TutorGroup
            tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
            tutor_groups = (await db.execute(tg_stmt)).scalars().all()
            
            # If tutor, we must filter by these groups.
            # Easiest way? Fetch all groups then filter? Or rely on DB fallback?
            # Let's rely on DB fallback for consistency if HEMIS API doesn't support list-based group checking easily
            pass 
        else:
            spec_id = None
            if specialty_name:
                # [FIX] Smarter resolution using Faculty and Form context
                spec_id = await HemisService.resolve_specialty_id(
                    specialty_name, 
                    education_type,
                    faculty_id=faculty_id,
                    education_form=education_form
                )
    
            all_groups = await HemisService.get_group_list(
                faculty_id=faculty_id,
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
    f_id = getattr(staff, 'faculty_id', None)
    s_role = getattr(staff, 'role', None)
    
    filters = [
        Student.university_id == uni_id, 
        Student.group_number != None
    ]
    
    # Role-based restriction
    if s_role == 'tyutor':
        from database.models import TutorGroup
        tg_stmt = select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
        group_numbers = (await db.execute(tg_stmt)).scalars().all()
        filters.append(Student.group_number.in_(group_numbers))
    elif f_id:
        filters.append(Student.faculty_id == f_id)
        
    if faculty_id: filters.append(Student.faculty_id == faculty_id)
    if level_name: filters.append(Student.level_name == level_name)
        
    result = await db.execute(select(Student.group_number).where(and_(*filters)).distinct().order_by(Student.group_number))
    groups = result.scalars().all()
    
    return {"success": True, "data": groups}

@router.get("/students/{student_id}/full-details")
async def get_mgmt_student_details(
    student_id: int,
    staff: Any = Depends(get_current_staff),
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
    type: str = "document",
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends the document file to the management user's Telegram bot.
    """
    from database.models import UserDocument, UserCertificate
    from bot import bot
    
    # Security
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR]
    is_mgmt = getattr(staff, 'hemis_role', None) == 'rahbariyat' or getattr(staff, 'role', None) in global_mgmt_roles or getattr(staff, 'role', None) == StaffRole.TYUTOR
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat yoki tyutorlar uchun")
    
    # 1. Get Document/Certificate and Student Info
    if type == "certificate":
        stmt = (
            select(UserCertificate, Student)
            .join(Student, UserCertificate.student_id == Student.id)
            .where(UserCertificate.id == doc_id)
        )
    else:
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
        # Determine caption and file type safely
        category = getattr(doc, 'category', 'Sertifikat')
        file_type = getattr(doc, 'file_type', 'document')
        
        caption = (
            f"📄 <b>Talaba Hujjati (Rahbariyat)</b>\n\n"
            f"Talaba: <b>{student.full_name}</b>\n"
            f"Guruh: <b>{student.group_number}</b>\n"
            f"Hujjat: <b>{doc.title}</b>\n"
            f"Kategoriya: <b>{category}</b>"
        )
        
        if file_type == 'photo':
            await bot.send_photo(
                chat_id=tg_acc.chat_id,
                photo=doc.file_id,
                caption=caption,
                parse_mode='HTML'
            )
        else:
             await bot.send_document(
                chat_id=tg_acc.chat_id,
                document=doc.file_id,
                caption=caption,
                parse_mode='HTML'
            )
            
        return {"success": True, "message": "Hujjat botga yuborildi"}
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
    staff: Any = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all student documents for management with filtering.
    """
    from database.models import UserDocument, UserCertificate
    
    # 1. Security & Role Resolution
    global_mgmt_roles = [StaffRole.RAHBARIYAT, StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR]
    staff_role = getattr(staff, 'role', None) or getattr(staff, 'hemis_role', None)
    is_mgmt = staff_role == 'rahbariyat' or staff_role in global_mgmt_roles or staff_role == StaffRole.TYUTOR
    
    if not is_mgmt:
        raise HTTPException(status_code=403, detail="Faqat rahbariyat uchun")
        
    uni_id = getattr(staff, 'university_id', None)
    if not uni_id:
        raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # 2. Auto-restrict Faculty/Group for Dean/Tutor
    # If Dean, override faculty_id to their own
    if staff_role == 'dekan':
        faculty_id = getattr(staff, 'faculty_id', None)
    # If Tutor, restrict via group lookup (TutorGroup)
    if staff_role == 'tyutor':
        from database.models import TutorGroup
        tutor_groups = await db.execute(select(TutorGroup.group_name).where(TutorGroup.staff_id == staff.id))
        tutor_group_names = tutor_groups.scalars().all()
        # If specific group not requested, filter by all tutor's groups
        if not group_number and tutor_group_names:
            group_number = tutor_group_names[0] # Simplification for now

    # 3. Base category filters
    category_filters = [Student.university_id == uni_id]
    if faculty_id: category_filters.append(Student.faculty_id == faculty_id)
    if education_type: category_filters.append(Student.education_type == education_type)
    if education_form: category_filters.append(Student.education_form == education_form)
    if level_name: category_filters.append(Student.level_name == level_name)
    if specialty_name: category_filters.append(Student.specialty_name == specialty_name)
    if group_number: category_filters.append(Student.group_number == group_number)

    all_results = []
    total_count = 0

    # 4. Fetch Certificates (If title="Sertifikatlar" or "Hammasi")
    if not title or title == "Sertifikatlar":
        stmt_cert = select(UserCertificate).join(Student).where(and_(*category_filters)).options(selectinload(UserCertificate.student))
        if query:
            stmt_cert = stmt_cert.where((UserCertificate.title.ilike(f"%{query}%")) | (Student.full_name.ilike(f"%{query}%")))
        
        # Count for Certificates
        cnt_cert = await db.execute(select(func.count(UserCertificate.id)).join(Student).where(and_(*category_filters)))
        total_count += cnt_cert.scalar() or 0
        
        res_cert = await db.execute(stmt_cert.order_by(UserCertificate.created_at.desc()))
        for c in res_cert.scalars().all():
            all_results.append({
                "id": f"cert_{c.id}",
                "title": c.title,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "file_id": c.file_id,
                "file_type": "document",
                "is_certificate": True,
                "student": {
                    "full_name": c.student.full_name if c.student else "Noma'lum",
                    "group_number": c.student.group_number if c.student else "",
                    "faculty_name": c.student.faculty_name if c.student else "",
                }
            })

    # 5. Fetch Standard Documents (If title mismatch "Sertifikatlar")
    if title != "Sertifikatlar":
        stmt_doc = select(UserDocument).join(Student).where(and_(*category_filters)).options(selectinload(UserDocument.student))
        if title:
            stmt_doc = stmt_doc.where(UserDocument.title == title)
        if query:
            stmt_doc = stmt_doc.where((UserDocument.title.ilike(f"%{query}%")) | (Student.full_name.ilike(f"%{query}%")))
            
        # Count for Documents
        cnt_doc = await db.execute(select(func.count(UserDocument.id)).join(Student).where(and_(*category_filters)))
        total_count += cnt_doc.scalar() or 0
        
        res_doc = await db.execute(stmt_doc.order_by(UserDocument.created_at.desc()))
        for d in res_doc.scalars().all():
            all_results.append({
                "id": str(d.id),
                "title": d.title,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "file_id": d.file_id,
                "file_type": d.file_type or "document",
                "student": {
                    "full_name": d.student.full_name if d.student else "Noma'lum",
                    "group_number": d.student.group_number if d.student else "",
                    "faculty_name": d.student.faculty_name if d.student else "",
                }
            })

    # 6. Sort Combined Results & Paginate
    all_results.sort(key=lambda x: x["created_at"] or "", reverse=True)
    
    start = (page - 1) * limit
    paginated_results = all_results[start : start + limit]
    
    return {
        "success": True, 
        "data": paginated_results, 
        "total_count": total_count
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
    # If title is "Sertifikatlar", fetch from UserCertificate table
    if title == "Sertifikatlar":
        from database.models import UserCertificate
        
        category_filters = [Student.university_id == uni_id]
        if f_id: category_filters.append(Student.faculty_id == f_id)
        elif faculty_id: category_filters.append(Student.faculty_id == faculty_id)
        # Note: Certificates might not have strict education/group filters but we apply what we can if joined logic allows
        # For simplicity, we filter by student relation
        
        stmt = (
            select(UserCertificate, Student)
            .join(Student, UserCertificate.student_id == Student.id)
            .where(and_(*category_filters))
        )
        
        if query:
             stmt = stmt.where(
                (UserCertificate.title.ilike(f"%{query}%")) |
                (Student.full_name.ilike(f"%{query}%"))
            )
        
        stmt = stmt.order_by(UserCertificate.created_at.desc())
        
    else:
        # Standard Documents Query
        category_filters = [Student.university_id == uni_id]
        
        if f_id: category_filters.append(Student.faculty_id == f_id)
        elif faculty_id: category_filters.append(Student.faculty_id == faculty_id)
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
                            f_type = getattr(doc, 'file_type', 'document') # Default to document behavior if missing (likely has path ext)
                            
                            if f_type == "document" or "." in file_path:
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


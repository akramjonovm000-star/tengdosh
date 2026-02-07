from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any

from api.dependencies import get_current_student, get_db
from database.models import Student, Staff, TgAccount, UserActivity
from database.models import StaffRole

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

    # 2. Total Students in University
    total_students = await db.scalar(
        select(func.count(Student.id)).where(Student.university_id == uni_id)
    ) or 0

    # 3. Platform Users (Students with TgAccount)
    # We join Student and TgAccount to filter by university
    platform_users = await db.scalar(
        select(func.count(Student.id))
        .join(TgAccount, Student.id == TgAccount.student_id)
        .where(Student.university_id == uni_id)
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
    uni_id = getattr(staff, 'university_id', None)
    if not uni_id: raise HTTPException(status_code=400, detail="Universitet aniqlanmadi")

    # Show only faculties that have students
    result = await db.execute(
        select(Student.faculty_id, Student.faculty_name)
        .where(Student.university_id == uni_id, Student.faculty_id != None)
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
    # Unique levels for this faculty
    result = await db.execute(
        select(Student.level_name)
        .where(Student.faculty_id == faculty_id)
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
    # Unique groups for this faculty and level
    result = await db.execute(
        select(Student.group_number)
        .where(Student.faculty_id == faculty_id, Student.level_name == level_name)
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
    result = await db.execute(
        select(Student)
        .where(Student.group_number == group_number)
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
                "image_url": s.image_url
            } for s in students
        ]
    }

@router.get("/students/search")
async def search_mgmt_students(
    query: str,
    staff: Any = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    uni_id = getattr(staff, 'university_id', None)
    
    stmt = select(Student).where(Student.university_id == uni_id)
    
    # Simple search by Name, Hemis ID or Hemis Login
    stmt = stmt.where(
        (Student.full_name.ilike(f"%{query}%")) | 
        (Student.hemis_id.ilike(f"%{query}%")) |
        (Student.hemis_login.ilike(f"%{query}%"))
    ).limit(50)
    
    result = await db.execute(stmt)
    students = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": s.id, 
                "full_name": s.full_name, 
                "hemis_id": s.hemis_id,
                "image_url": s.image_url,
                "group_number": s.group_number
            } for s in students
        ]
    }

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

        # 1. Appeales (Feedbacks)
        appeals_result = await db.execute(
            select(StudentFeedback).where(StudentFeedback.student_id == student_id, StudentFeedback.parent_id == None)
        )
        appeals = appeals_result.scalars().all()

        # 2. Activities
        activities_result = await db.execute(
            select(UserActivity).where(UserActivity.student_id == student_id)
        )
        activities = activities_result.scalars().all()

        # 3. Documents
        docs_result = await db.execute(
            select(UserDocument).where(UserDocument.student_id == student_id)
        )
        docs = docs_result.scalars().all()

        # 4. Certificates
        certs_result = await db.execute(
            select(UserCertificate).where(UserCertificate.student_id == student_id)
        )
        certs = certs_result.scalars().all()

        def safe_isoformat(dt):
            return dt.isoformat() if dt else None

        return {
            "success": True,
            "data": {
                "profile": {
                    "id": student.id,
                    "full_name": student.full_name,
                    "hemis_id": student.hemis_id,
                    "faculty_name": student.faculty_name,
                    "group_number": student.group_number,
                    "image_url": student.image_url,
                    "phone": student.phone
                },
                "appeals": [{"id": a.id, "text": a.text, "status": a.status, "date": safe_isoformat(a.created_at)} for a in appeals],
                "activities": [{"id": act.id, "title": act.title, "status": act.status, "date": safe_isoformat(act.created_at)} for act in activities],
                "documents": [{"id": d.id, "title": d.title, "status": d.status, "date": safe_isoformat(d.created_at)} for d in docs],
                "certificates": [{"id": c.id, "title": c.title, "status": c.status, "date": safe_isoformat(c.created_at)} for c in certs]
            }
        }
    except Exception as e:
        import traceback
        print(f"ERROR in get_mgmt_student_details: {e}")
        traceback.print_exc()
        return {"success": False, "message": str(e)}

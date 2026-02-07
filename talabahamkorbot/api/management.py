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

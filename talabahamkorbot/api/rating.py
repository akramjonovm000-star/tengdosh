from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime

from api.dependencies import get_current_student, get_db
from api.schemas import RatingStatusSchema, RatingTargetSchema, RatingSubmitSchema
from database.models import Student, Staff, StaffRole, TutorGroup, RatingActivation, RatingRecord

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/active", response_model=RatingStatusSchema)
async def get_active_ratings(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Check which rating categories are active for the student's university.
    """
    query = select(RatingActivation).where(
        RatingActivation.university_id == student.university_id,
        RatingActivation.is_active == True
    )
    result = await db.execute(query)
    activations = result.scalars().all()
    
    active_roles = [a.role_type for a in activations]
    expires_at = activations[0].expires_at if activations else None
    questions = activations[0].questions if activations else []
    
    return {
        "is_active": len(active_roles) > 0,
        "active_roles": active_roles,
        "questions": questions,
        "expires_at": expires_at
    }

@router.get("/targets/{role_type}", response_model=list[RatingTargetSchema])
async def get_rating_targets(
    role_type: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of persons to rate for an active role.
    - If tutor: Only the student's group tutor.
    - If dean/vice_dean: Deans/Vice Deans of student's faculty.
    """
    # 1. Verify if role_type is active for this university
    act_query = select(RatingActivation).where(
        RatingActivation.university_id == student.university_id,
        RatingActivation.role_type == role_type,
        RatingActivation.is_active == True
    )
    act_res = await db.execute(act_query)
    if not act_res.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Ushbu yo'nalishda baholash faol emas")

    targets = []
    
    if role_type == "tutor":
        # Find Tutor linked via TutorGroup
        if not student.group_number:
            return []
            
        tg_query = select(TutorGroup).where(
            TutorGroup.university_id == student.university_id,
            TutorGroup.group_number == student.group_number
        ).options(selectinload(TutorGroup.tutor))
        
        tg_res = await db.execute(tg_query)
        tg = tg_res.scalar_one_or_none()
        
        if tg and tg.tutor:
            targets.append(RatingTargetSchema(
                staff_id=tg.tutor.id,
                full_name=tg.tutor.full_name,
                image_url=tg.tutor.image_url,
                role_name="Guruh tyutori"
            ))
            
    elif role_type in ["dean", "vice_dean"]:
        # Find Dean or Vice Dean for student's faculty
        role_map = {
            "dean": [StaffRole.DEKAN],
            "vice_dean": [StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR]
        }
        target_roles = role_map.get(role_type, [])
        
        staff_query = select(Staff).where(
            Staff.university_id == student.university_id,
            Staff.faculty_id == student.faculty_id,
            Staff.role.in_(target_roles),
            Staff.is_active == True
        )
        staff_res = await db.execute(staff_query)
        staffs = staff_res.scalars().all()
        
        for s in staffs:
            role_display = "Dekan" if s.role == StaffRole.DEKAN else "Dekan o'rinbosari"
            targets.append(RatingTargetSchema(
                staff_id=s.id,
                full_name=s.full_name,
                image_url=None,
                role_name=role_display
            ))

    return targets

@router.post("/submit")
async def submit_rating(
    req: RatingSubmitSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Anonymously submit a rating (1-5 targets). 
    Enforces one-rating-per-student-per-person rule.
    """
    # 1. Basic validation
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(status_code=400, detail="Baho 1-5 oralig'ida bo'lishi kerak")
        
    # 2. Check if already rated this person
    check_query = select(RatingRecord).where(
        RatingRecord.user_id == student.id,
        RatingRecord.rated_person_id == req.rated_person_id
    )
    check_res = await db.execute(check_query)
    if check_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Siz ushbu shaxsni allaqachon baholagansiz")
        
    # 3. Save rating
    new_record = RatingRecord(
        user_id=student.id,
        rated_person_id=req.rated_person_id,
        role_type=req.role_type,
        university_id=student.university_id,
        rating=req.rating,
        answers=req.answers or []
    )
    db.add(new_record)
    await db.commit()
    
    return {"status": "success", "message": "Bahoyingiz qabul qilindi. Rahmat!"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List

from database.models import Staff, StaffRole, RatingRecord, Faculty, RatingActivation
from api.dependencies import get_current_staff, get_db
from api.schemas import StaffRatingStatsSchema, RatingStatsBreakdownSchema, RatingActivationToggleSchema

router = APIRouter()

@router.get("/stats", response_model=List[StaffRatingStatsSchema])
async def get_rating_stats(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Get rating statistics for Rahbariyat (Management).
    - Rektors/Prorektors: See all stats in the university.
    - Dekans/Vice Deans: See only Tutors in their faculty.
    """
    # 1. Determine access scope
    is_top_admin = staff.role in [
        StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR,
        StaffRole.OWNER, StaffRole.DEVELOPER
    ]
    is_faculty_admin = staff.role in [
        StaffRole.DEKAN, StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR
    ]
    
    if not (is_top_admin or is_faculty_admin):
        raise HTTPException(status_code=403, detail="Sizda ushbu ma'lumotlarni ko'rish huquqi yo'q")

    # 2. Query target staff members to show stats for
    staff_query = select(Staff).where(
        Staff.university_id == staff.university_id,
        Staff.is_active == True
    )
    
    if is_faculty_admin and not is_top_admin:
        # Dekans only see Tutors of their own faculty
        staff_query = staff_query.where(
            Staff.faculty_id == staff.faculty_id,
            Staff.role == StaffRole.TYUTOR
        )
    else:
        # Top admins see everyone (Deans AND Tutors) who have ratings
        # We can broaden this if needed, but per request, they see "barcha fakultetlar boyicha"
        pass

    staff_res = await db.execute(staff_query)
    target_staff_list = staff_res.scalars().all()
    
    results = []
    
    for s in target_staff_list:
        # 3. Calculate Average and Count for this person
        # We use a subquery/aggregate join for better performance, but here for small N it's okay
        stats_query = select(
            func.avg(RatingRecord.rating),
            func.count(RatingRecord.id)
        ).where(RatingRecord.rated_person_id == s.id)
        
        stats_res = await db.execute(stats_query)
        avg_rating, total_votes = stats_res.one()
        
        if total_votes == 0:
            continue # No data yet, skip to avoid cluttering

        # 4. Calculate Breakdown (1-5)
        breakdown = []
        for r_val in range(1, 6):
            b_query = select(func.count(RatingRecord.id)).where(
                and_(RatingRecord.rated_person_id == s.id, RatingRecord.rating == r_val)
            )
            b_res = await db.execute(b_query)
            count = b_res.scalar()
            
            breakdown.append(RatingStatsBreakdownSchema(
                rating=r_val,
                count=count,
                percentage=round((count / total_votes * 100), 1) if total_votes > 0 else 0
            ))
            
        role_label = str(s.role.value if hasattr(s.role, 'value') else s.role).capitalize()
        
        results.append(StaffRatingStatsSchema(
            staff_id=s.id,
            full_name=s.full_name,
            image_url=s.image_url,
            role_name=role_label,
            average_rating=round(float(avg_rating), 1) if avg_rating else 0.0,
            total_votes=total_votes,
            breakdown=breakdown
        ))
        
    # Sort by average rating descending
    results.sort(key=lambda x: x.average_rating, reverse=True)
    
    return results

@router.get("/status")
async def get_rating_activation_status(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if tutor rating is active for the user's university.
    """
    query = select(RatingActivation).where(
        RatingActivation.university_id == staff.university_id,
        RatingActivation.role_type == 'tutor'
    )
    result = await db.execute(query)
    activation = result.scalar_one_or_none()
    
    return {
        "is_active": activation.is_active if activation else False
    }

@router.post("/activate")
async def toggle_rating_activation(
    req: RatingActivationToggleSchema,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate/Deactivate a rating category.
    """
    # 1. Permission check
    is_authorized = staff.role in [
        StaffRole.REKTOR, StaffRole.PROREKTOR, StaffRole.YOSHLAR_PROREKTOR,
        StaffRole.OWNER, StaffRole.DEVELOPER, StaffRole.DEKAN
    ]
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Sizda ushbu amalni bajarish huquqi yo'q")

    # 2. Find or Create activation record
    query = select(RatingActivation).where(
        RatingActivation.university_id == staff.university_id,
        RatingActivation.role_type == req.role_type
    )
    result = await db.execute(query)
    activation = result.scalar_one_or_none()

    if activation:
        activation.is_active = req.is_active
    else:
        activation = RatingActivation(
            university_id=staff.university_id,
            role_type=req.role_type,
            is_active=req.is_active
        )
        db.add(activation)

    await db.commit()
    return {"success": True, "is_active": activation.is_active}

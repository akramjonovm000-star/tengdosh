from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

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
        "is_active": activation.is_active if activation else False,
        "title": activation.title if activation else None,
        "description": activation.description if activation else None,
        "questions": activation.questions if activation else [],
        "expires_at": activation.expires_at if activation else None
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
        StaffRole.OWNER, StaffRole.DEVELOPER, StaffRole.DEKAN,
        StaffRole.DEKAN_ORINBOSARI, StaffRole.DEKAN_YOSHLAR, StaffRole.RAHBARIYAT,
        StaffRole.DEKANAT, StaffRole.YOSHLAR_YETAKCHISI, StaffRole.YOSHLAR_ITTIFOQI,
        StaffRole.INSPEKTOR, StaffRole.PSIXOLOG
    ]
    if not is_authorized:
        raise HTTPException(status_code=403, detail=f"Sizda ({staff.role}) ushbu amalni bajarish huquqi yo'q")

    # 2. Find or Create activation record
    activation = None
    if req.id:
        # Update existing by ID
        query = select(RatingActivation).where(
            RatingActivation.id == req.id,
            RatingActivation.university_id == staff.university_id
        )
        result = await db.execute(query)
        activation = result.scalar_one_or_none()
        if not activation:
             raise HTTPException(status_code=404, detail="So'rovnoma topilmadi")
    else:
        # Create new check: 
        # Optional: if we want to allow only ONE active survey per role at a time, we could deactivate others.
        # But for now, just create a new one.
        pass

    if activation:
        activation.is_active = req.is_active
        if req.title: activation.title = req.title
        activation.role_type = req.role_type # Allow changing target role
        if req.description: activation.description = req.description
        if req.questions is not None: activation.questions = req.questions
        if req.end_at:
            try:
                activation.expires_at = datetime.strptime(req.end_at, '%Y-%m-%d %H:%M:%S')
            except:
                pass
    else:
        expires_at = None
        if req.end_at:
            try:
                expires_at = datetime.strptime(req.end_at, '%Y-%m-%d %H:%M:%S')
            except:
                pass
                
        activation = RatingActivation(
            university_id=staff.university_id,
            role_type=req.role_type,
            is_active=req.is_active,
            title=req.title,
            description=req.description,
            questions=req.questions or [],
            expires_at=expires_at
        )
        db.add(activation)

    await db.commit()
    await db.refresh(activation)
    return {
        "success": True, 
        "id": activation.id,
        "is_active": activation.is_active, 
        "message": "Muvaffaqiyatli saqlandi"
    }

@router.get("/list")
async def list_management_surveys(
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    List all rating surveys (activations) for management.
    """
    query = select(RatingActivation).where(
        RatingActivation.university_id == staff.university_id
    ).order_by(RatingActivation.created_at.desc())
    
    result = await db.execute(query)
    activations = result.scalars().all()
    
    surveys = []
    now = datetime.utcnow()
    
    for a in activations:
        # Determine status: active, pending, finished
        status = "pending"
        if a.is_active:
            if a.expires_at and a.expires_at < now:
                status = "finished"
            else:
                status = "active"
        
        # Calculate total votes for this specific activation
        # Note: RatingRecord needs a way to link to an activation if we want exact stats per period.
        # But currently RatingRecord only has role_type.
        # For now, let's return a global count per person or an aggregate count.
        # Actually, let's just return 0 or implement a better link later.
        
        surveys.append({
            "id": a.id,
            "title": a.title or f"So'rovnoma #{a.id}",
            "description": a.description,
            "role_type": a.role_type,
            "is_active": a.is_active,
            "status": status,
            "questions": a.questions or [],
            "start_at": a.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "end_at": a.expires_at.strftime('%Y-%m-%d %H:%M:%S') if a.expires_at else "Cheksiz",
            "total_votes": 0 # Placeholder
        })
        
    return surveys

@router.post("/update")
async def update_rating_activation(
    req: RatingActivationToggleSchema,
    staff: Staff = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db)
):
    """
    Alias for /activate to handle existing survey updates.
    """
    return await toggle_rating_activation(req, staff, db)

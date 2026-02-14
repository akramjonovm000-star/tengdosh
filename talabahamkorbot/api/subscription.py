from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from database.db_connect import AsyncSessionLocal
from database.models import Student, StudentSubscription, StudentNotification
from api.dependencies import get_current_student, get_db
from api.schemas import StudentProfileSchema
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/subscribe/{target_id}")
async def toggle_subscription(
    target_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle follow status:
    - If already following -> Unfollow
    - If not following -> Follow
    Returns: {"subscribed": bool, "followers_count": int}
    """
    if target_id == student.id:
        print(f"FAILED: Cannot follow self. {target_id} vs {student.id}")
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
        
    print(f"Subs Toggle: {student.id} -> {target_id}")
        
    target_student = await db.get(Student, target_id)
    if not target_student:
        raise HTTPException(status_code=404, detail="Target student not found")
        
    # Check existing
    existing = await db.scalar(
        select(StudentSubscription).where(
            StudentSubscription.follower_id == student.id,
            StudentSubscription.target_id == target_id
        )
    )
    
    subscribed = False
    
    if existing:
        # Unfollow
        await db.delete(existing)
        subscribed = False
    else:
        # Follow
        new_sub = StudentSubscription(
            follower_id=student.id,
            target_id=target_id
        )
        db.add(new_sub)
        subscribed = True
        
        # Send Notification to Target
        try:
            from services.notification_service import NotificationService
            # NotificationService is async? Or synchronous? Usually we just add DB record
            # Let's add DB record properly
            notif = StudentNotification(
                student_id=target_id,
                title="Yangi obunachi! 👤",
                body=f"{student.full_name} sizga obuna bo'ldi.",
                type="social" # New type
            )
            db.add(notif)
            # Potentially trigger FCM via background task/celery later, 
            # but for now let's rely on polling or direct DB insert which mobile picks up
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")

    await db.commit()
    
    # Get Updated Count
    count = await db.scalar(
        select(func.count(StudentSubscription.id)).where(StudentSubscription.target_id == target_id)
    )
    
    return {
        "subscribed": subscribed,
        "followers_count": count
    }

@router.get("/subscribers/count")
async def get_counts(
    target_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get followers and following count for a user"""
    followers = await db.scalar(
        select(func.count(StudentSubscription.id)).where(StudentSubscription.target_id == target_id)
    )
    following = await db.scalar(
        select(func.count(StudentSubscription.id)).where(StudentSubscription.follower_id == target_id)
    )
    return {"followers": followers, "following": following}

@router.get("/check-subscription/{target_id}")
async def check_subscription(
    target_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Check if current user follows target_id"""
    exists = await db.scalar(
        select(StudentSubscription).where(
            StudentSubscription.follower_id == student.id,
            StudentSubscription.target_id == target_id
        )
    )
    return {"subscribed": exists is not None}

def _map_student_profile(student: Student) -> dict:
    """Helper to convert Student model to response format expected by Mobile UI"""
    if not student:
        return {}
        
    # Start with Schema
    data = StudentProfileSchema.model_validate(student).model_dump()
    
    # Force 'image' and 'role' keys for frontend compatibility (Matches student.py logic)
    data['image'] = student.image_url
    data['role'] = student.hemis_role or "student"
    
    # Ensure image_url is also present
    if not data.get('image_url'):
        data['image_url'] = student.image_url
        
    # Format Name (Clean up parentheses and reorder)
    from utils.student_utils import format_name
    data['full_name'] = format_name(student.full_name)
        
    return data

@router.get("/followers-list/{target_id}")
async def get_followers_list(
    target_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get list of users following the target_id"""
    query = select(StudentSubscription).options(
        selectinload(StudentSubscription.follower)
    ).where(StudentSubscription.target_id == target_id)
    
    result = await db.execute(query)
    subs = result.scalars().all()
    
    # Return list of students mapped to profile schema
    return [_map_student_profile(s.follower) for s in subs]


@router.get("/following-list/{target_id}")
async def get_following_list(
    target_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get list of users target_id is following"""
    query = select(StudentSubscription).options(
        selectinload(StudentSubscription.target)
    ).where(StudentSubscription.follower_id == target_id)
    
    result = await db.execute(query)
    subs = result.scalars().all()
    
    # Return list of students mapped to profile schema
    return [_map_student_profile(s.target) for s in subs]

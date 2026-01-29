from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.db_connect import get_db
from database.models import StudentNotification
from api.dependencies import get_current_student, get_owner
from services.notification_service import NotificationService

router = APIRouter()

# Schema
class BroadcastSchema(BaseModel):
    title: str
    body: str
    data: Optional[dict] = None

# Schema
class TokenRegistrationSchema(BaseModel):
    fcm_token: str

# Schema
class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str
    type: str # 'grade', 'info', 'alert'
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/list", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = 0, 
    limit: int = 20, 
    student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(StudentNotification)
        .where(StudentNotification.student_id == student.id)
        .order_by(desc(StudentNotification.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/unread-count")
async def get_unread_count(
    student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db)
):
    # Using simple list count, optimization possible with count(*) query
    stmt = (
        select(StudentNotification)
        .where(StudentNotification.student_id == student.id, StudentNotification.is_read == False)
    )
    result = await session.execute(stmt)
    notifications = result.scalars().all()
    return {"count": len(notifications)}

@router.post("/{notif_id}/read")
async def mark_read(
    notif_id: int,
    student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db)
):
    notif = await session.get(StudentNotification, notif_id)
    if not notif or notif.student_id != student.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notif.is_read = True
    await session.commit()
    return {"status": "success"}

@router.post("/read-all")
async def mark_all_read(
    student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        update(StudentNotification)
        .where(StudentNotification.student_id == student.id, StudentNotification.is_read == False)
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success"}

@router.post("/register-token")
async def register_fcm_token(
    data: TokenRegistrationSchema,
    student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db)
):
    """Register or update FCM token for the student"""
    if not data.fcm_token:
        raise HTTPException(status_code=400, detail="Token is required")
        
    student.fcm_token = data.fcm_token
    await session.commit()
    return {"success": True, "message": "Token registered successfully"}

@router.post("/broadcast")
async def broadcast_push(
    data: BroadcastSchema,
    owner = Depends(get_owner)
):
    """Broadcast push notification to all users (Owner only)"""
    from services.notification_service import NotificationService
    
    # Offload to Celery
    NotificationService.run_broadcast.delay(
        title=data.title,
        body=data.body,
        data=data.data
    )
    
    return {"success": True, "message": "Broadcast initialized in background"}


from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from typing import List
from datetime import datetime

from api.dependencies import get_current_user, get_db
from database.models import Announcement, AnnouncementRead, User

router = APIRouter(prefix="/announcements", tags=["Announcements"])

@router.get("/")
async def get_announcements(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch unread announcements for the user.
    If priority >= 100 (Superadmin), they might be forced or always show first.
    """
    # 1. Get IDs of announcements already read by user
    read_stmt = select(AnnouncementRead.announcement_id).where(AnnouncementRead.user_id == user.id)
    read_res = await db.execute(read_stmt)
    read_ids = read_res.scalars().all()

    # 2. Fetch active announcements
    now = datetime.utcnow()
    stmt = (
        select(Announcement)
        .where(
            and_(
                Announcement.is_active == True,
                or_(Announcement.expires_at == None, Announcement.expires_at > now),
                or_(Announcement.university_id == None, Announcement.university_id == user.university_id)
            )
        )
        .where(~Announcement.id.in_(read_ids) if read_ids else True)
        .order_by(desc(Announcement.priority), desc(Announcement.created_at))
    )
    
    res = await db.execute(stmt)
    announcements = res.scalars().all()
    
    return {
        "success": True,
        "data": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "image_url": a.image_url,
                "link": a.link,
                "priority": a.priority,
                "created_at": a.created_at.isoformat()
            }
            for a in announcements
        ]
    }

@router.post("/{announcement_id}/read")
async def mark_as_read(
    announcement_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an announcement as read.
    """
    # Check if already read
    stmt = select(AnnouncementRead).where(
        and_(AnnouncementRead.user_id == user.id, AnnouncementRead.announcement_id == announcement_id)
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    
    if not existing:
        new_read = AnnouncementRead(user_id=user.id, announcement_id=announcement_id)
        db.add(new_read)
        await db.commit()
    
    return {"success": True}

@router.post("/create")
async def create_announcement(
    title: str = Body(...),
    content: str = Body(None),
    image_url: str = Body(None),
    link: str = Body(None),
    priority: int = Body(0),
    expires_at: str = Body(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin only: Create new announcement.
    """
    if user.role not in ["admin", "owner", "developer"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    exp_dt = None
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at)
        except:
            pass

    new_a = Announcement(
        title=title,
        content=content,
        image_url=image_url,
        link=link,
        priority=priority,
        expires_at=exp_dt
    )
    db.add(new_a)
    await db.commit()
    await db.refresh(new_a)
    
    return {"success": True, "id": new_a.id}

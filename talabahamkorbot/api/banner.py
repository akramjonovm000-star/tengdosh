
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from api.dependencies import get_db
from database.models import Banner

router = APIRouter(prefix="/banner", tags=["Banner"])


from services.banner_analytics import BannerAnalyticsService

@router.get("/active")
async def get_active_banner(
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch the currently active banner.
    Returns the latest created banner that is_active=True.
    """
    stmt = (
        select(Banner)
        .where(Banner.is_active == True)
        .order_by(desc(Banner.id))
        .limit(1)
    )
    result = await db.execute(stmt)
    banner = result.scalar_one_or_none()
    
    
    # Increment view count via buffer
    if banner:
        await BannerAnalyticsService().increment_view(banner.id)
    
    if not banner:
        return {"active": False}
        
    return {
        "id": banner.id,
        "active": True,
        "image_file_id": banner.image_file_id,
        "link": banner.link,
        "created_at": banner.created_at.isoformat()
    }

@router.post("/click/{banner_id}")
async def track_banner_click(
    banner_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Increment click count for a banner
    """
    await BannerAnalyticsService().increment_click(banner_id)
    return {"status": "ok"}

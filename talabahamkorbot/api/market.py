from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.db_connect import get_session
from database.models import Student, MarketItem, MarketCategory
from api.dependencies import get_current_student

router = APIRouter(prefix="/market", tags=["market"])

# --- Schemas ---
class MarketItemCreate(BaseModel):
    title: str
    description: str
    price: str
    category: MarketCategory
    image_url: Optional[str] = None
    contact_phone: Optional[str] = None
    telegram_username: Optional[str] = None

class MarketItemResponse(BaseModel):
    id: int
    title: str
    description: str
    price: Optional[str]
    category: str
    image_url: Optional[str]
    views_count: int
    created_at: datetime
    is_my: bool = False
    student_name: str
    contact_phone: Optional[str]
    telegram_username: Optional[str]

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("", response_model=List[MarketItemResponse])
async def get_market_items(
    cat: Optional[MarketCategory] = None,
    sort: str = "newest", # newest, popular, oldest
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    # MAINTENANCE MODE - Return fake item as banner
    from datetime import datetime
    
    dummy_item = MarketItemResponse(
        id=0,
        title="🚀 TEZ KUNDA!",
        description="Bozor bo'limi tez kunlarda ishga tushadi! Biz siz uchun ajoyib imkoniyatlarni tayyorlamoqdamiz.",
        price="---",
        category="Boshqa",
        image_url=None,
        views_count=0,
        created_at=datetime.now(),
        is_my=False,
        student_name="Tengdosh Jamoasi",
        contact_phone=None,
        telegram_username="talabahamkor"
    )
    
    return [dummy_item]

    # Legacy Logic Halted
    # stmt = select(MarketItem).options(joinedload(MarketItem.student)).where(MarketItem.is_active == True)
    # ... (rest hidden) ...
    # return resp_list

@router.post("", response_model=MarketItemResponse)
async def create_market_item(
    req: MarketItemCreate,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    raise HTTPException(
        status_code=503, 
        detail="Bozor bo'limi tez kunlarda ishga tushadi! Hozircha e'lon qo'shish imkoni mavjud emas."
    )
    
    # new_item = MarketItem(...)

@router.delete("/{item_id}")
async def delete_market_item(
    item_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    item = await db.get(MarketItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="E'lon topilmadi")
        
    if item.student_id != student.id:
        raise HTTPException(status_code=403, detail="Bu e'lon sizniki emas")
        
    await db.delete(item)
    await db.commit()
    return {"success": True, "message": "O'chirildi"}

@router.post("/{item_id}/view")
async def view_market_item(
    item_id: int,
    db: AsyncSession = Depends(get_session)
):
    item = await db.get(MarketItem, item_id)
    if item:
        item.views_count += 1
        await db.commit()
    return {"success": True}

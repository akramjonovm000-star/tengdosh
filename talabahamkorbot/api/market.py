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
    stmt = select(MarketItem).options(joinedload(MarketItem.student)).where(MarketItem.is_active == True)
    
    # Sorting Logic
    if sort == "popular":
        stmt = stmt.order_by(desc(MarketItem.views_count), desc(MarketItem.created_at))
    elif sort == "oldest":
        stmt = stmt.order_by(MarketItem.created_at)
    else: # newest
        stmt = stmt.order_by(desc(MarketItem.created_at))
    
    if cat:
        stmt = stmt.where(MarketItem.category == cat.value)
    
    if search:
        stmt = stmt.where(MarketItem.title.ilike(f"%{search}%"))
        
    stmt = stmt.limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    resp_list = []
    for item in items:
        resp_list.append(MarketItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            price=item.price,
            category=item.category,
            image_url=item.image_url,
            views_count=item.views_count,
            created_at=item.created_at,
            is_my=(item.student_id == student.id),
            student_name=item.student.full_name, # Accessing relationship safe now
            contact_phone=item.contact_phone or item.student.phone,
            telegram_username=item.telegram_username
        ))
        
    return resp_list

@router.post("", response_model=MarketItemResponse)
async def create_market_item(
    req: MarketItemCreate,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    new_item = MarketItem(
        student_id=student.id,
        title=req.title,
        description=req.description,
        price=req.price,
        category=req.category.value,
        image_url=req.image_url,
        contact_phone=req.contact_phone,
        telegram_username=req.telegram_username,
        is_active=True
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    return MarketItemResponse(
        id=new_item.id,
        title=new_item.title,
        description=new_item.description,
        price=new_item.price,
        category=new_item.category,
        image_url=new_item.image_url,
        views_count=0,
        created_at=new_item.created_at,
        is_my=True,
        student_name=student.full_name,
        contact_phone=new_item.contact_phone,
        telegram_username=new_item.telegram_username
    )

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

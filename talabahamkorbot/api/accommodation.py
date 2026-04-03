from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update, or_
from sqlalchemy.orm import joinedload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.db_connect import get_session
from database.models import Student, MarketItem, MarketCategory, DormitoryIssue, DormitoryRule, DormitoryRoster, DormitoryMenu
from api.dependencies import get_current_student

router = APIRouter(prefix="/accommodation", tags=["accommodation"])

# --- Housing Schemas ---
class AccommodationListingResponse(BaseModel):
    id: int
    title: str
    description: str
    price: Optional[str]
    category: str
    image_url: Optional[str]
    image_urls: List[str] = []
    address: Optional[str]
    views_count: int
    created_at: datetime
    is_my: bool = False
    student_name: str
    contact_phone: Optional[str]
    telegram_username: Optional[str]
    university_name: Optional[str]

    class Config:
        from_attributes = True

class CreateAccommodationListingRequest(BaseModel):
    title: str
    description: str
    price: Optional[str]
    address: Optional[str]
    contact_phone: Optional[str]
    telegram_username: Optional[str]

# --- Dormitory Schemas ---
class DormRoommateResponse(BaseModel):
    id: int
    full_name: str
    group_number: Optional[str]
    image_url: Optional[str]

class DormIssueResponse(BaseModel):
    id: int
    category: str
    description: str
    image_urls: List[str] = []
    status: str
    created_at: datetime

class CreateDormIssueRequest(BaseModel):
    category: str
    description: str

class DormRuleResponse(BaseModel):
    id: int
    title: str
    content: str
    importance: str

class DormMenuResponse(BaseModel):
    id: int
    day_name: str
    breakfast: Optional[str]
    lunch: Optional[str]
    dinner: Optional[str]

class DormRosterResponse(BaseModel):
    id: int
    student_name: str
    day_of_week: str
    duty_type: str

# --- Housing Endpoints ---

@router.get("/listings", response_model=List[AccommodationListingResponse])
async def get_accommodation_listings(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Fetch all housing/roommate listings"""
    stmt = (
        select(MarketItem)
        .options(joinedload(MarketItem.student))
        .where(MarketItem.category == MarketCategory.HOUSING.value)
        .where(MarketItem.is_active == True)
        .order_by(desc(MarketItem.created_at))
    )
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    resp_list = []
    for item in items:
        resp_list.append(AccommodationListingResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            price=item.price,
            category=item.category,
            image_url=item.image_url,
            image_urls=item.image_urls or [],
            address=item.address,
            views_count=item.views_count,
            created_at=item.created_at,
            is_my=(item.student_id == student.id),
            student_name=item.student.full_name,
            contact_phone=item.contact_phone,
            telegram_username=item.telegram_username,
            university_name=item.student.university_name
        ))
    
    return resp_list

@router.post("/listings")
async def create_accommodation_listing(
    req: CreateAccommodationListingRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Create a new housing ad"""
    new_item = MarketItem(
        student_id=student.id,
        title=req.title,
        description=req.description,
        price=req.price,
        address=req.address,
        contact_phone=req.contact_phone,
        telegram_username=req.telegram_username,
        category=MarketCategory.HOUSING.value,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    return {"success": True, "id": new_item.id}

# --- Dormitory Endpoints ---

@router.get("/dorm/roommates", response_model=List[DormRoommateResponse])
async def get_dorm_roommates(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Find other students in the same room/building based on accommodation_name string"""
    if not student.accommodation_name or "Talabalar turar joyida" not in student.accommodation_name:
        return []
        
    # Heuristic: Find others with the EXACT same accommodation string (usually house + room)
    stmt = (
        select(Student)
        .where(Student.accommodation_name == student.accommodation_name)
        .where(Student.id != student.id)
    )
    result = await db.execute(stmt)
    roommates = result.scalars().all()
    return roommates

@router.get("/dorm/rules", response_model=List[DormRuleResponse])
async def get_dorm_rules(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(DormitoryRule))
    return result.scalars().all()

@router.get("/dorm/menu", response_model=List[DormMenuResponse])
async def get_dorm_menu(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(DormitoryMenu))
    return result.scalars().all()

@router.get("/dorm/roster", response_model=List[DormRosterResponse])
async def get_dorm_roster(db: AsyncSession = Depends(get_session)):
    stmt = (
        select(DormitoryRoster)
        .options(joinedload(DormitoryRoster.student))
        .order_by(DormitoryRoster.id)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return [
        DormRosterResponse(
            id=item.id,
            student_name=item.student.full_name,
            day_of_week=item.day_of_week,
            duty_type=item.duty_type
        ) for item in items
    ]

@router.post("/dorm/issue")
async def report_dorm_issue(
    req: CreateDormIssueRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    new_issue = DormitoryIssue(
        student_id=student.id,
        category=req.category,
        description=req.description,
        status="pending"
    )
    db.add(new_issue)
    await db.commit()
    await db.refresh(new_issue)
    return {"success": True, "id": new_issue.id}

@router.get("/dorm/my-issues", response_model=List[DormIssueResponse])
async def get_my_dorm_issues(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    stmt = (
        select(DormitoryIssue)
        .where(DormitoryIssue.student_id == student.id)
        .order_by(desc(DormitoryIssue.created_at))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

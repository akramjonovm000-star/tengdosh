from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta

from database.db_connect import get_session
from database.models import Student
from api.dependencies import get_current_student, get_db

router = APIRouter()

class PlanSchema(BaseModel):
    id: str
    name: str
    price_uzs: int
    duration_days: int
    description: str

PLANS = [
    PlanSchema(id="monthly", name="Bir oylik", price_uzs=10000, duration_days=30, description="1 oy davomida cheklovsiz imkoniyatlar"),
    PlanSchema(id="quarterly", name="Uch oylik", price_uzs=25000, duration_days=90, description="3 oy davomida cheklovsiz imkoniyatlar"),
    PlanSchema(id="halfyear", name="Olti oylik", price_uzs=50000, duration_days=180, description="6 oy davomida cheklovsiz imkoniyatlar (Arzonroq)"),
    PlanSchema(id="yearly", name="Bir yillik", price_uzs=100000, duration_days=365, description="1 yil davomida cheklovsiz imkoniyatlar (Eng arzon)")
]

@router.get("", response_model=List[PlanSchema])
async def get_plans():
    return PLANS

@router.post("/buy/{plan_id}")
async def buy_plan(
    plan_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    plan = next((p for p in PLANS if p.id == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Tarif topilmadi")
        
    if student.balance < plan.price_uzs:
        raise HTTPException(status_code=400, detail="Balansingizda mablag' yetarli emas")
        
    # Deduct Balance
    student.balance -= plan.price_uzs
    
    # Activate Premium
    now = datetime.utcnow()
    # If already active, extend
    if student.is_premium and student.premium_expiry and student.premium_expiry > now:
        student.premium_expiry += timedelta(days=plan.duration_days)
    else:
        student.is_premium = True
        student.premium_expiry = now + timedelta(days=plan.duration_days)
        
    # Reset AI Usage & Set Paid Limit
    student.ai_limit = 25
    if not student.ai_usage_count: student.ai_usage_count = 0
    
    await db.commit()
    
    return {
        "status": "success", 
        "message": f"{plan.name} muvaffaqiyatli faollashtirildi!",
        "new_balance": student.balance,
        "expiry": student.premium_expiry.isoformat()
    }

@router.post("/trial")
async def activate_trial(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    if student.trial_used:
        raise HTTPException(status_code=400, detail="Siz avval sinov davridan foydalangansiz")
        
    if student.is_premium:
        raise HTTPException(status_code=400, detail="Sizda allaqachon Premium mavjud")
        
    # Activate 1 Week Trial
    try:
        student.trial_used = True
        student.is_premium = True
        student.premium_expiry = datetime.utcnow() + timedelta(days=7)
        
        # Set Trial Limit
        student.ai_limit = 5
        student.ai_usage_count = 0
        
        await db.commit()
        return {"status": "success", "message": "1 haftalik bepul sinov davri faollashtirildi!"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

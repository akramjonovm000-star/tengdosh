from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.templating import Jinja2Templates
from database.db_connect import get_db
from database.models import Student, Staff, Banner, TgAccount

import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

@router.get("/webapp/dashboard/{telegram_id}")
async def get_student_dashboard(
    request: Request, 
    telegram_id: int, 
    session: AsyncSession = Depends(get_db)
):
    """
    Serves the Student Dashboard Web App.
    """
    # 1. Fetch User
    # In production, we should validate initData hash!
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == telegram_id))
    
    user_data = None
    if account:
        if account.student_id:
            student = await session.get(Student, account.student_id)
            if student:
                user_data = {
                    "full_name": student.full_name,
                    "short_name": student.short_name,
                    "image_url": student.image_url,
                    "role": "student"
                }

    if not user_data:
        # Fallback for testing or non-registered users
        user_data = {
            "full_name": "Mehmon",
            "short_name": "Mehmon", 
            "image_url": None,
            "role": "guest"
        }

    # 2. Fetch Active Banners
    banners = (await session.execute(select(Banner).where(Banner.is_active == True).order_by(Banner.id.desc()))).scalars().all()
    
    banner_list = []
    for b in banners:
        # Prepare data for JS
        banner_list.append({
            "image_url": b.image_file_id if b.image_file_id.startswith("http") else "https://placehold.co/900x1600/007aff/ffffff/png?text=Placeholder", # Handle file_id vs url
            "link": b.link,
            "id": b.id
        })

    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "user": user_data,
            "banners": banner_list
        }
    )

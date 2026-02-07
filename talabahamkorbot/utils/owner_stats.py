
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    University, Faculty, Staff, Student, 
    TgAccount, UserActivity, UserActivityImage, 
    UserDocument, StudentFeedback, UserAppeal
)

# Simple Cache for Owner Dashboard
_dashboard_cache = {
    "text": None,
    "expiry": None
}

async def get_owner_dashboard_text(session: AsyncSession) -> str:
    """
    Owner paneli uchun statistik ma'lumotlarni yig'ib,
    tayyor matn ko'rinishida qaytaradi.
    Kesh: 5 daqiqa.
    """
    global _dashboard_cache
    now = datetime.utcnow()
    
    if _dashboard_cache["text"] and _dashboard_cache["expiry"] > now:
        return _dashboard_cache["text"]
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    month_ago = now - timedelta(days=30)
    
    # 1. Total Counts
    total_staff = await session.scalar(select(func.count(Staff.id))) or 0
    total_students = await session.scalar(select(func.count(Student.id))) or 0
    
    # 2. Telegram Accounts (Verified Users)
    total_tg = await session.scalar(select(func.count(TgAccount.id))) or 0
    
    text = (
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"• Talabalar: <b>{total_students}</b>\n"
        f"• Xodimlar: <b>{total_staff}</b>\n"
        f"• Bot foydalanuvchilari: <b>{total_tg}</b>"
    )
    
    _dashboard_cache["text"] = text
    _dashboard_cache["expiry"] = now + timedelta(minutes=1) # Reduced cache time
    
    return text

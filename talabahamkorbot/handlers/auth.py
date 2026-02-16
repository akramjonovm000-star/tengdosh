from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TgAccount, Student, Staff, User

async def get_current_user(telegram_id: int, session: AsyncSession):
    """
    Retrieves the current user (Student or Staff) based on Telegram ID.
    """
    # 1. Try TgAccount
    result = await session.execute(
        select(TgAccount)
        .options(selectinload(TgAccount.student), selectinload(TgAccount.staff))
        .where(TgAccount.telegram_id == telegram_id)
    )
    account = result.scalar_one_or_none()
    
    if account:
        if account.current_role == "student" and account.student:
            return account.student
        if account.current_role == "staff" and account.staff:
             return account.staff
        
        # Fallback: Prefer Staff if available, then Student
        if account.staff: return account.staff
        if account.student: return account.student

    return None

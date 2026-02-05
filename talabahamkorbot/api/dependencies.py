from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_token_data(authorization: str = Header(None)):
    """
    Parses token. Returns dict: {"type": "telegram"|"student", "id": int}
    """
    import logging
    logger = logging.getLogger(__name__)
    if not authorization:
        logger.warning(f"Auth failed: Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    logger.info(f"Checking auth header: {authorization[:25]}...")
    token = authorization.replace("Bearer ", "")
    
    if token.startswith("jwt_token_for_"):
        try:
            tid = int(token.replace("jwt_token_for_", ""))
            return {"type": "telegram", "id": tid}
        except:
             pass


    if token.startswith("student_id_"):
        try:
            sid = int(token.replace("student_id_", ""))
            return {"type": "student", "id": sid}
        except:
            pass

    if token.startswith("staff_id_"):
        try:
            sid = int(token.replace("staff_id_", ""))
            return {"type": "staff", "id": sid}
        except:
            pass
            
    logger.error(f"Auth failed: Invalid Token Format: {authorization[:25]}")
    raise HTTPException(status_code=401, detail="Invalid Token Format")

async def get_current_user_id(token_data: dict = Depends(get_current_user_token_data)):
    # Legacy support if needed, but better to use token_data directly
    return token_data["id"]

from database.models import Staff

async def get_current_staff(
    token_data: dict = Depends(get_current_user_token_data),
    db: AsyncSession = Depends(get_db)
):
    if token_data["type"] != "staff":
        raise HTTPException(status_code=403, detail="Faqat xodimlar uchun")
        
    staff = await db.get(Staff, token_data["id"])
    if not staff:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
        
    return staff

async def get_current_student(
    token_data: dict = Depends(get_current_user_token_data),
    db: AsyncSession = Depends(get_db)
):
    try:
        if token_data["type"] == "telegram":
            # Lookup via TgAccount
            tg_acc = await db.scalar(select(TgAccount).where(TgAccount.telegram_id == token_data["id"]))
            if not tg_acc or not tg_acc.student_id:
                raise HTTPException(status_code=404, detail="Student not found (TG)")
            student = await db.get(Student, tg_acc.student_id)
        elif token_data["type"] == "student":
            # Direct Student ID
            student = await db.get(Student, token_data["id"])
        else:
             raise HTTPException(status_code=403, detail="Faqat talabalar uchun")

        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
            
        # --- AUTO-EXPIRATION CHECK ---
        from datetime import datetime
        if student.is_premium and student.premium_expiry:
            if student.premium_expiry < datetime.utcnow():
                student.is_premium = False
                
                from database.models import StudentNotification
                notif = StudentNotification(
                    student_id=student.id,
                    title="⚠️ Premium muddati tugadi",
                    body="Sizning Premium obunangiz muddati tugadi. Imkoniyatlarni qayta tiklash uchun hisobingizni to'ldiring.",
                    type="alert"
                )
                db.add(notif)
                await db.commit()
                
        return student
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_current_student: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

async def get_premium_student(student: Student = Depends(get_current_student)):
    """
    Dependency to ensure the student has active premium.
    """
    if not student.is_premium:
        raise HTTPException(
            status_code=403, 
            detail="Premium obuna talab etiladi. Iltimos, obunani faollashtiring."
        )
    return student

async def get_owner(student: Student = Depends(get_current_student)):
    """
    Dependency to ensure the student is an owner/admin.
    """
    if student.role != 'owner':
        raise HTTPException(
            status_code=403, 
            detail="Bu amal uchun ruxsat yo'q. Faqat adminlar uchun."
        )
    return student


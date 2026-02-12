from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student, User, StudentNotification

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
    
    logger.debug(f"Checking auth header: {authorization[:25]}...")
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
        elif token_data["type"] == "staff":
            # Staff ID - Return Staff object (Duck typing for basic user fields)
            from database.models import Staff
            student = await db.get(Staff, token_data["id"])
        else:
            raise HTTPException(status_code=403, detail="Faqat talabalar uchun")

        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
            
        # --- AUTO-EXPIRATION LOGIC (STUDENT ONLY) ---
        from datetime import datetime, timedelta
        if hasattr(student, 'is_premium') and student.is_premium and student.premium_expiry:
            # If expired for more than 7 days, remove premium and clear username
            if student.premium_expiry + timedelta(days=7) < datetime.utcnow():
                student.is_premium = False
                
                # Clear username if exists (Only for Students who have username field)
                if hasattr(student, 'username') and student.username:
                    from database.models import TakenUsername
                    username_entry = await db.scalar(select(TakenUsername).where(TakenUsername.student_id == student.id))
                    if username_entry:
                        await db.delete(username_entry)
                    student.username = None
                
                notif = StudentNotification(
                    student_id=student.id,
                    title="🚫 Premium va Username bekor qilindi",
                    body="Imtiyozli 7 kunlik muddat tugadi. Premium va @username o'chirildi.",
                    type="alert"
                )
                db.add(notif)
                await db.commit()
            elif student.premium_expiry + timedelta(days=3) < datetime.utcnow():
                # Features are closed (handled by get_premium_student), but we might want a one-time notification
                pass
            elif student.premium_expiry < datetime.utcnow():
                # Just expired, but in 3-day grace period
                pass
                
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
    Dependency to ensure the student has active premium (with 3-day grace period for general features).
    """
    from datetime import datetime, timedelta
    
    if not getattr(student, 'is_premium', False):
        raise HTTPException(
            status_code=403, 
            detail="Premium obuna talab etiladi. Iltimos, obunani faollashtiring."
        )
        
    # Check 3-day grace period for general features
    if student.premium_expiry and student.premium_expiry + timedelta(days=3) < datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail="Premium muddati va 3 kunlik imtiyoz o'tib ketgan. Funksiyalarni ochish uchun obunani yangilang."
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


async def get_current_user(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the User model instance corresponding to the currently authenticated student/staff.
    Reuses get_current_student to handle multiple auth types.
    """
    user = await db.scalar(select(User).where(User.hemis_login == student.hemis_login))
    if not user:
        # Fallback for staff who might not have hemis_login sync'd yet or differently
        user = await db.scalar(select(User).where(User.full_name == student.full_name))
        
    if not user:
        raise HTTPException(status_code=401, detail="Unified User record not found")
    return user


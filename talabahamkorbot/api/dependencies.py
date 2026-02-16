from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student, User, StudentNotification

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_token_data(
    request: Request = None, 
    authorization: str = Header(None)
):
    """
    Parses token. Returns dict: {"type": "telegram"|"student"|"staff", "id": int, "hemis_token": str|None}
    """
    import logging
    from api.security import verify_token, hash_user_agent
    
    logger = logging.getLogger(__name__)
    if not authorization:
        # logger.warning(f"Auth failed: Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # logger.debug(f"Checking auth header: {authorization[:10]}...")
    token = authorization.replace("Bearer ", "")
    
    # 1. Try JWT Verification (New Standard)
    payload = verify_token(token)
    if payload:
        # User-Agent Binding Check
        if request and "ua" in payload:
            current_ua = request.headers.get("user-agent", "unknown")
            expected_hash = payload["ua"]
            actual_hash = hash_user_agent(current_ua)
            
            if expected_hash != actual_hash:
                 logger.warning(f"Security Alert: Token User-Agent Mismatch! Expected: {expected_hash}, Actual: {actual_hash} (UA: {current_ua})")
                 raise HTTPException(status_code=401, detail="Xavfsizlik: Token boshqa qurilmada foydalanilmoqda!")

        if "type" in payload and "id" in payload:
             return {
                 "type": payload["type"], 
                 "id": payload["id"],
                 "hemis_token": payload.get("hemis_token") # [NEW] Extract embedded token
             }
             
    # 2. Legacy Formats (Backward Compatibility - Limited)
    # These users will fail any request requiring HEMIS token
    if token.startswith("jwt_token_for_"):
        try:
            tid = int(token.replace("jwt_token_for_", ""))
            return {"type": "telegram", "id": tid, "hemis_token": None}
        except:
             pass

    if token.startswith("student_id_"):
        try:
            sid = int(token.replace("student_id_", ""))
            return {"type": "student", "id": sid, "hemis_token": None}
        except:
            pass

    if token.startswith("staff_id_"):
        try:
            sid = int(token.replace("staff_id_", ""))
            return {"type": "staff", "id": sid, "hemis_token": None}
        except:
            pass
            
    # logger.error(f"Auth failed: Invalid Token Format")
    raise HTTPException(status_code=401, detail="Invalid Token Format")

async def get_current_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    return authorization.replace("Bearer ", "")

async def get_current_user_id(token_data: dict = Depends(get_current_user_token_data)):
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
    
    # [NEW] Inject Token from JWT (Stateless)
    if token_data.get("hemis_token"):
        staff.hemis_token = token_data["hemis_token"]
        
    return staff

async def get_current_student(
    token_data: dict = Depends(get_current_user_token_data),
    db: AsyncSession = Depends(get_db)
):
    if token_data["type"] != "student":
        raise HTTPException(status_code=403, detail="Faqat talabalar uchun")
        
    student = await db.get(Student, token_data["id"])
    if not student:
        raise HTTPException(status_code=404, detail="Talaba topilmadi")

    # [NEW] Inject Token from JWT (Stateless)
    if token_data.get("hemis_token"):
        student.hemis_token = token_data["hemis_token"]
    
    # Fallback: If DB has it (migration phase), use it? 
    # No, we commented out the column in models, so accessing student.hemis_token 
    # might actually return None or fail if SQLAlchemy didn't map it.
    # But since we commented it out in models.py, 'student' object won't have the attribute populated from DB.
    # So we MUST inject it here.
    
    return student
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


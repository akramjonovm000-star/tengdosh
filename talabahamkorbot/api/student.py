from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_current_student, get_db, get_premium_student
from api.schemas import StudentProfileSchema
from database.models import Student, TgAccount
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/me")
@router.get("/me/")
async def get_my_profile(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get the currently logged-in student's profile."""
    # Ensure consistency with auth.py
    
    # [FIX] Handle Staff Profile (Tyutor/Dean)
    # Staff objects don't match StudentProfileSchema
    from database.models import Staff
    if isinstance(student, Staff):
        # Allow hemis_login fallback
        h_login = getattr(student, 'hemis_login', '')
        
        return {
             "id": student.id,
             "full_name": student.full_name,
             "first_name": student.full_name.split()[0] if student.full_name else "",
             "last_name": student.full_name.split()[-1] if student.full_name and len(student.full_name.split()) > 1 else "",
             "short_name": student.full_name, # Fallback
             "role": "Xodim", # Generic staff label or specific
             "role_code": student.role, # Internal code
             "image": getattr(student, 'image_url', None) or "https://ui-avatars.com/api/?name=" + student.full_name.replace(" ", "+"),
             "image_url": getattr(student, 'image_url', None) or "https://ui-avatars.com/api/?name=" + student.full_name.replace(" ", "+"),
             "university_name": getattr(student, 'university_name', "JMCU"),
             "faculty_name": "",
             "specialty_name": student.position,
             "group_number": "",
             "level_name": "",
             "semester_name": "",
             "education_form": "",
             "student_status": "active" if student.is_active else "inactive",
             "hemis_id": str(student.hemis_id) if student.hemis_id else None,
             "hemis_login": h_login,
             "is_premium": getattr(student, 'is_premium', False),
             "premium_expiry": student.premium_expiry.isoformat() if student.premium_expiry else None,
             "custom_badge": getattr(student, 'custom_badge', None),
             "is_registered_bot": False # Simplification
        }

    data = StudentProfileSchema.model_validate(student).model_dump()
    
    # Parse first/last names from full_name if available
    fn = (student.full_name or "").strip()
    if fn and len(fn.split()) >= 2:
        parts = fn.split()
        data['last_name'] = parts[0].title()
        data['first_name'] = parts[1].title()
    else:
        # Fallback
        data['first_name'] = student.short_name or student.full_name
        data['last_name'] = ""

    data['university_name'] = student.university_name
    
    data['university_name'] = student.university_name
    
    # [FIX] Role Mapping
    role_map = {
        "student": "Talaba",
        "teacher": "O'qituvchi", 
        "tyutor": "Tyutor",
        "rahbariyat": "Rahbariyat",
        "admin": "Admin",
        "staff": "Xodim",
        "owner": "Tizim Egasi"
    }
    
    raw_role = student.hemis_role or "student"
    data['role'] = role_map.get(raw_role, "Foydalanuvchi")
    
    # Override for specific cases if needed
    if raw_role == "student":
        data['role'] = "Talaba"
    
    # Force 'image' key for frontend compatibility
    # Ensure HTTPS
    raw_image = student.image_url
    if raw_image and raw_image.startswith("http://"):
        raw_image = raw_image.replace("http://", "https://")
        
    data['image'] = raw_image 
    if not data.get('image_url'):
        data['image_url'] = raw_image

    # Check Telegram Registration
    tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
    data['is_registered_bot'] = True if tg_acc else False
    
    # [NEW] Opportunistic Prefetch for existing users (Triggered on App Start)
    # This ensures users who are ALREADY logged in get the benefit of cache warming
    # without needing to re-login.
    import asyncio
    from services.hemis_service import HemisService
    asyncio.create_task(HemisService.prefetch_data(student.hemis_token, student.id))

    return data


@router.post("/sync")
async def sync_data(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Force synchronization of Hemis data.
    Useful for 'Pull to Refresh' or error recovery.
    """
    import asyncio
    from services.hemis_service import HemisService
    
    # Trigger background prefetch
    asyncio.create_task(HemisService.prefetch_data(student.hemis_token, student.id))
    
    return {"success": True, "message": "Ma'lumotlar yangilanmoqda..."}



from fastapi import UploadFile, File, Request
import shutil
import time
import os

@router.post("/image")
async def upload_profile_image(
    request: Request,
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and set a custom profile image for the student.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG: Received upload request. Filename: {file.filename}, Content-Type: {file.content_type}")

    try:
        # Validate Image
        if not file.content_type.startswith("image/"):
             logger.warning(f"DEBUG: Invalid content type: {file.content_type}")
             return {"success": False, "message": "Faqat rasm yuklash mumkin"}
        
        # --- DELETE OLD IMAGE START ---
        if student.image_url:
            try:
                # Url: http://host/static/uploads/filename.ext
                # We need to find "static/uploads/filename.ext"
                if "static/uploads/" in student.image_url:
                    parts = student.image_url.split("static/uploads/")
                    if len(parts) > 1:
                        old_filename = parts[1]
                        old_file_path = f"static/uploads/{old_filename}"
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                            print(f"Deleted old avatar: {old_file_path}")
            except Exception as cleanup_error:
                print(f"Error cleaning up old image: {cleanup_error}")
        # --- DELETE OLD IMAGE END ---

        # Create Filename
        ext = file.filename.split(".")[-1]
        filename = f"{student.id}_{int(time.time())}.{ext}"
        file_path = f"static/uploads/{filename}"
        
        # Save File
        abs_path = os.path.abspath(file_path)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"DEBUG: Saving file {file.filename} ({file.content_type}) to {abs_path}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        size = os.path.getsize(file_path)
        logger.info(f"DEBUG: File saved. Size: {size} bytes")
            
        # Build URL - Better protocol handling
        from config import DOMAIN
        
        # Use https for images to ensure visibility on mobile (Mixed Content)
        full_url = f"https://{DOMAIN}/{file_path}"
        logger.info(f"DEBUG: Generated URL: {full_url}")
        
        # Update DB
        student.image_url = full_url
        await db.commit()
        
        return {
            "success": True,
            "data": {
                "image_url": full_url
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Server xatosi: {str(e)}"}

from api.schemas import UsernameUpdateSchema
import re
from fastapi import HTTPException, Header

@router.post("/username")
async def set_username(
    data: UsernameUpdateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Set or update username"""
    # [NEW] Premium Check
    from datetime import datetime
    if not student.is_premium or not student.premium_expiry or student.premium_expiry < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Username o'rnatish yoki o'zgartirish faqat Premium foydalanuvchilar uchun")

    raw_username = data.username.strip()
    if raw_username.startswith("@"):
        raw_username = raw_username[1:]
    username_lower = raw_username.lower()
    
    # Validation
    if not (5 <= len(raw_username) <= 32):
        raise HTTPException(status_code=400, detail="Username kamida 5 ta harfdan iborat bo'lishi kerak")
        
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", raw_username):
        raise HTTPException(status_code=400, detail="Username faqat lotin harflari, raqamlar va _ dan iborat bo'lishi va harf bilan boshlanishi kerak")
    
    # Check uniqueness in TakenUsername table
    from database.models import TakenUsername
    
    # Check if this exact username is taken by someone else (using lowercase for uniqueness)
    existing = await db.scalar(select(TakenUsername).where(TakenUsername.username == username_lower))
    
    if existing:
        if existing.student_id != student.id:
            raise HTTPException(status_code=400, detail="Bu username allaqachon olingan")
        else:
            # Already mine, just check if casing changed
            if student.username != raw_username:
                 student.username = raw_username
                 await db.commit()
            return {"success": True, "username": raw_username}
            
    # If I had an old username, we want to update the existing record for THIS student
    # This avoids "duplicate key value violates unique constraint" on student_id
    current_taken = await db.scalar(select(TakenUsername).where(TakenUsername.student_id == student.id))
    
    if current_taken:
        # Update existing record
        current_taken.username = username_lower
    else:
        # Insert new (always lowercase for uniqueness)
        new_taken = TakenUsername(username=username_lower, student_id=student.id)
        db.add(new_taken)
    
    # Update Student record (store Mixed Case)
    student.username = raw_username
    
    # Also sync to Users table (if exists)
    from database.models import User
    user_record = await db.scalar(select(User).where(User.hemis_login == student.hemis_login))
    if user_record:
        user_record.username = raw_username
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Xatolik: {str(e)}")
    
    return {"success": True, "username": raw_username}

@router.get("/check-username")
async def check_username_availability(
    username: str,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Check if username is available (True if available)"""
    username = username.strip().lower()
    if not username: 
        return {"available": False}
        
    from database.models import TakenUsername
    existing = await db.scalar(select(TakenUsername).where(TakenUsername.username == username))
    
    if existing and authorization:
        # If taken, check if it's ME
        try:
            token = authorization.replace("Bearer ", "")
            student_id = None
            if token.startswith("student_id_"):
                # DEV/TEST Token
                student_id = int(token.replace("student_id_", ""))
            elif token.startswith("jwt_token_for_"):
                # TG Token
                tid = int(token.replace("jwt_token_for_", ""))
                tg_acc = await db.scalar(select(TgAccount).where(TgAccount.telegram_id == tid))
                if tg_acc:
                    student_id = tg_acc.student_id
            
            if student_id and existing.student_id == student_id:
                return {"available": True}
        except:
             pass
    
    return {"available": existing is None}

from sqlalchemy import or_
from fastapi_cache.decorator import cache
from pydantic import BaseModel

@router.get("/search")
# Cache reduced to 1 second to fetch fresh avatar/name updates immediately
@cache(expire=1)
async def search_students(
    query: str,
    db: AsyncSession = Depends(get_db)
):
    """Search students by username or name"""
    query = query.strip()
    if len(query) < 2:
        return []
        
    if query.startswith("@"):
        query = query[1:]
        
    search_term = f"%{query}%"
    
    # Priority: Username match > Name match
    # We can just fetch all matches
    stmt = select(Student).where(
        or_(
            Student.username.ilike(search_term),
            Student.full_name.ilike(search_term)
        )
    ).limit(20)
    
    result = await db.execute(stmt)
    students = result.scalars().all()
    
    from utils.student_utils import format_name
    
    encoded = []
    for s in students:
        data = StudentProfileSchema.model_validate(s).model_dump()
        # Override name with friendly format
        data['full_name'] = format_name(s.full_name)
        
        # Ensure HTTPS for images
        raw_image = s.image_url
        if raw_image and raw_image.startswith("http://"):
            raw_image = raw_image.replace("http://", "https://")
            
        data['image'] = raw_image 
        if not data.get('image_url'):
            data['image_url'] = raw_image
        data['avatar'] = raw_image # Alias for frontend compatibility
        
        # ensure role passed
        data['role'] = s.hemis_role or "student"
        encoded.append(data)
        
    return encoded

class BadgeUpdateSchema(BaseModel):
    emoji: str

@router.put("/badge")
async def update_badge(
    data: BadgeUpdateSchema,
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_db)
):
    """Set custom badge (Premium only)"""
    # Simple validation (emoji)
    if not data.emoji or len(data.emoji) > 4: 
         raise HTTPException(status_code=400, detail="Noto'g'ri emoji. Iltimos bitta emoji tanlang.")
         
    student.custom_badge = data.emoji
    await db.commit()
    
    return {"success": True, "badge": data.emoji}

@router.get("/{student_id}")
async def get_student_public_profile(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public profile of another student by ID.
    Used when viewing someone else's profile.
    """
    s = await db.get(Student, student_id)
    if not s:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Validation logic similar to /me but limited
    data = StudentProfileSchema.model_validate(s).model_dump()
    
    # Format Name 
    from utils.student_utils import format_name
    data['full_name'] = format_name(s.full_name)
    
    # Image logic (Force HTTPS)
    raw_image = s.image_url
    if raw_image and raw_image.startswith("http://"):
        raw_image = raw_image.replace("http://", "https://")
        
    data['image'] = raw_image 
    if not data.get('image_url'):
        data['image_url'] = raw_image
    data['avatar'] = raw_image # Alias for frontend compatibility

    # Calculate Role
    data['role'] = s.hemis_role or "student"
    
    # Check registration (for badge/status if needed)
    tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == s.id))
    data['is_registered_bot'] = True if tg_acc else False
    
    return data

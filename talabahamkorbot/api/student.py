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
    data['role'] = student.hemis_role or "student" # Populate role for Mobile UI
    
    # Force 'image' key for frontend compatibility
    data['image'] = student.image_url 
    if not data.get('image_url'):
        data['image_url'] = student.image_url

    # Check Telegram Registration
    tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
    data['is_registered_bot'] = True if tg_acc else False
    
    return data

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
        base_url = str(request.base_url).rstrip("/")
        if base_url.endswith("/api/v1"):
            base_url = base_url[:-7] # Remove /api/v1
        
        # Check scheme from X-Forwarded-Proto if proxy middleware didn't catch it
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        if "://" in base_url:
            current_scheme = base_url.split("://")[0]
            base_url = base_url.replace(f"{current_scheme}://", f"{scheme}://")

        full_url = f"{base_url}/{file_path}"
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
from fastapi import HTTPException

@router.post("/username")
async def set_username(
    data: UsernameUpdateSchema,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Set or update username"""
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
    db: AsyncSession = Depends(get_db)
):
    """Check if username is available (True if available)"""
    username = username.strip().lower()
    if not username: 
        return {"available": False}
        
    from database.models import TakenUsername
    existing = await db.scalar(select(TakenUsername).where(TakenUsername.username == username))
    
    return {"available": existing is None}

from sqlalchemy import or_
from fastapi_cache.decorator import cache
from pydantic import BaseModel

@router.get("/search")
@cache(expire=300) # [NEW] Cache for 5 mins
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
        data['image'] = s.image_url # Ensure image key needed by mobile
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

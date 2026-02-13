from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from api.dependencies import get_current_student, get_premium_student, get_db
from api.schemas import ActivityListSchema
from database.models import Student, UserActivity, UserActivityImage
from bot import bot

router = APIRouter()

from sqlalchemy.orm import selectinload
from database.models import PendingUpload, TgAccount, Student
from models.states import ActivityUploadState
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

# Helper to set FSM state manually
async def set_bot_state(user_id: int, state):
    # We need to access FSM storage directly
    # Ideally reuse Dispatcher logic, but simplified here:
    from bot import dp, bot
    from config import BOT_TOKEN
    
    bot_id = bot.id
    if bot_id is None:
        try:
            bot_id = int(BOT_TOKEN.split(":")[0])
        except:
            print("Failed to derive bot_id from token")
            
    # Construct StorageKey
    key = StorageKey(bot_id=bot_id, chat_id=user_id, user_id=user_id)
    
    # Convert state object to string if needed
    state_str = state.state if hasattr(state, "state") else str(state)
    
    # Set state
    await dp.storage.set_state(key, state_str)

@router.get("/")
@router.get("")
async def get_my_activities(
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_db)
):
    """List all activities for the current student."""
    activities = await db.scalars(
        select(UserActivity)
        .where(UserActivity.student_id == student.id)
        .order_by(desc(UserActivity.id))
        .options(selectinload(UserActivity.images))
    )
    return activities.all()

@router.post("/upload/init")
async def init_upload_session(
    session_id: str = Form(...),
    category: str = Form("Faollik"), # NEW
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize a new upload session.
    1. Create PendingUpload record.
    2. Notify User via Bot.
    3. Set User State in Bot.
    """
    
    # 1. Check TG Account
    tg_acc = await db.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
    if not tg_acc:
        raise HTTPException(status_code=400, detail="Telegram account not linked")

    # 2. Create Pending Record
    # Remove old pending for this session if exists
    existing = await db.get(PendingUpload, session_id)
    if existing:
        await db.delete(existing)
    
    new_pending = PendingUpload(
        session_id=session_id,
        student_id=student.id,
        file_ids="" # Empty initially
    )
    db.add(new_pending)
    await db.commit()

    # 3. Notify & Set State
    try:
        msg_text = (
            f"📸 <b>{category} uchun rasm yuklang!</b>\n\n"
            f"Iltimos, <b>{category}</b>ga oid rasmlarni yuboring.\n"
            "<i>(Maksimal 5 ta rasm qabul qilinadi)</i>"
        )
        
        await bot.send_message(
            chat_id=tg_acc.telegram_id,
            text=msg_text,
            parse_mode="HTML"
        )
        
        # Set State
        await set_bot_state(tg_acc.telegram_id, ActivityUploadState.waiting_for_photo)
        
    except Exception as e:
        print(f"Failed to notify user: {e}")

    return {"status": "initialized", "session_id": session_id}


@router.get("/upload/status/{session_id}")
async def check_upload_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Check if file has been uploaded for this session."""
    pending = await db.get(PendingUpload, session_id)
    
    if not pending:
        raise HTTPException(status_code=404, detail="Session not found")
        
    current_ids = [fid for fid in pending.file_ids.split(",") if fid]
    count = len(current_ids)
    
    if count > 0:
        return {
            "status": "uploaded", 
            "count": count,
            "file_ids": current_ids
        }
    
    return {"status": "pending", "count": 0}


@router.post("/")
@router.post("")
async def create_activity(
    category: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    date: str = Form(...),
    session_id: str = Form(None), # LINK TO UPLOADED FILE
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Create activity using PRE-UPLOADED file from Telegram.
    """
    
    # 1. Create Activity Record
    new_act = UserActivity(
        student_id=student.id,
        category=category,
        name=name,
        description=description,
        date=date,
        status="pending"
    )
    db.add(new_act)
    await db.flush()
    
    saved_images = []

    # 2. Check Session & File
    if session_id:
        pending = await db.get(PendingUpload, session_id)
        if pending and pending.file_ids:
            file_ids = [fid for fid in pending.file_ids.split(",") if fid]
            
            for fid in file_ids:
                db.add(UserActivityImage(
                    activity_id=new_act.id,
                    file_id=fid,
                    file_type="photo"
                ))
                saved_images.append(fid)
            
            # Optional: Cleanup pending record? 
            # await db.delete(pending) 
            # Keeping it for logs might be safer for now.

    await db.commit()
    await db.refresh(new_act)

    image_response = [{"file_id": fid} for fid in saved_images]
    
    return {
        "id": new_act.id,
        "category": new_act.category,
        "name": new_act.name,
        "description": new_act.description,
        "date": new_act.date,
        "status": new_act.status,
        "images": image_response
    }


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific activity."""
    act = await db.get(UserActivity, activity_id)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    if act.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not your activity")
        
    # Delete images from DB (Cascade should handle it if configured, but let's be safe)
    # SQLAlchemy relationship cascade="all, delete" usually handles this if model is set up right.
    # UserActivity model -> images = relationship(..., cascade="all, delete-orphan")
    
    await db.delete(act)
    await db.commit()
    
    return {"status": "deleted", "id": activity_id}


@router.patch("/{activity_id}")
async def update_activity(
    activity_id: int,
    category: str = Form(None),
    name: str = Form(None),
    description: str = Form(None),
    date: str = Form(None),
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_db)
):
    """Update activity details (Partial)."""
    # Eager load images to prevent them from disappearing in response
    result = await db.execute(
        select(UserActivity)
        .where(UserActivity.id == activity_id)
        .options(selectinload(UserActivity.images))
    )
    act = result.scalars().first()
    
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    if act.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not your activity")
        
    if category: act.category = category
    if name: act.name = name
    if description: act.description = description
    if date: act.date = date
    
    # Optional: Reset status to pending if it was rejected
    if act.status == "rejected":
        act.status = "pending"
        
    await db.commit()
    await db.refresh(act)
    
    return {
        "id": act.id,
        "category": act.category,
        "name": act.name,
        "description": act.description,
        "date": act.date,
        "status": act.status
    }

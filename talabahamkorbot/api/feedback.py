from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from api.dependencies import get_current_student, get_db
from api.schemas import FeedbackListSchema, AppealListResponseSchema, AppealStatsSchema
from database.models import Student, StudentFeedback, FeedbackReply, TgAccount, PendingUpload

from bot import bot
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Feedback"])

from models.states import FeedbackStates
from aiogram.fsm.storage.base import StorageKey

async def set_bot_state(user_id: int, state):
    from bot import dp, bot
    from config import BOT_TOKEN
    
    bot_id = bot.id
    if bot_id is None:
        try:
            bot_id = int(BOT_TOKEN.split(":")[0])
        except:
            logger.error("Failed to derive bot_id from token")
            
    key = StorageKey(bot_id=bot_id, chat_id=user_id, user_id=user_id)
    # Convert state object to string if needed
    state_str = state.state if hasattr(state, "state") else str(state)
    await dp.storage.set_state(key, state_str)

class MessageSchema(BaseModel):
    id: int
    sender: str # 'me', 'staff', 'system'
    text: Optional[str]
    time: str
    file_id: Optional[str]

class FeedbackDetailSchema(BaseModel):
    id: int
    title: str
    recipient: str
    status: str
    date: str
    is_anonymous: bool
    messages: List[MessageSchema]

@router.get("/debug")
async def debug_feedbacks(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to check DB content"""
    # Count My Feedbacks
    start = datetime.utcnow()
    stmt = select(StudentFeedback).where(StudentFeedback.student_id == student.id)
    result = await db.execute(stmt)
    my_feedbacks = result.scalars().all()
    
    # Count All Feedbacks (Global)
    result_all = await db.execute(select(StudentFeedback))
    all_feedbacks = result_all.scalars().all()
    
    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "my_feedbacks_count": len(my_feedbacks),
        "total_feedbacks_in_db": len(all_feedbacks),
        "server_time": start.strftime("%H:%M:%S"),
        "sample_titles": [f.title for f in my_feedbacks[:3]] if hasattr(my_feedbacks[0] if my_feedbacks else None, 'title') else "ORMTitlesNotAvailable" # This checks if title is populated (it won't be in ORM, but we check if DB has data)
    }

@router.get("", response_model=List[FeedbackListSchema])
async def get_my_feedback(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """List all feedback/appeals sent by the student."""
    # DEBUG LOG
    logger.debug(f"DEBUG: get_my_feedback for student {student.id}")
    
    feedbacks = await db.scalars(
        select(StudentFeedback)
        .where(
            StudentFeedback.student_id == student.id,
            StudentFeedback.parent_id == None # Only root appeals
        )
        .order_by(desc(StudentFeedback.id))
    )
    results = feedbacks.all()
    
    response_list = []
    
    for fb in results:
        # 1. Compute Title
        display_title = f"Murojaat #{fb.id}"
        if fb.text:
             clean_text = fb.text.replace("\n", " ").strip()
             if clean_text:
                 display_title = clean_text[:30] + "..." if len(clean_text) > 30 else clean_text
        
        # 2. Build Dict (Safer than modifying ORM object)
        images_list = []
        if fb.file_id:
            images_list.append({
                "file_id": fb.file_id,
                "file_type": fb.file_type or "photo"
            })
            
        # 3. Calculate Department/Recipient for Filtering (Strict 6 Categories)
        role_map = {
            "rektor": "Rahbariyat",
            "prorektor": "Rahbariyat",
            "yoshlar_prorektor": "Rahbariyat",
            "rahbariyat": "Rahbariyat",
            "dekan": "Dekanat",
            "dekan_orinbosari": "Dekanat",
            "dekan_yoshlar": "Dekanat",
            "dekanat": "Dekanat",
            "tyutor": "Tyutor",
            "psixolog": "Psixolog",
            "inspektor": "Inspektor",
            "kutubxona": "Kutubxona"
        }
        raw_role = (fb.assigned_role or "").lower()
        dept = role_map.get(raw_role, "Boshqa")

        item = {
            "id": fb.id,
            "text": fb.text,
            "title": display_title,
            "department": dept,
            "recipient": dept, # For display on the card
            "status": fb.status,
            "assigned_role": dept, # For strict filtering in the app
            "created_at": fb.created_at, 
            "is_anonymous": fb.is_anonymous,
            "file_id": fb.file_id,
            "images": images_list
        }
        response_list.append(item)

    return response_list

@router.get("/stats", response_model=AppealStatsSchema)
async def get_feedback_stats(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get status statistics for the student's appeals."""
    feedbacks = await db.scalars(
        select(StudentFeedback)
        .where(
            StudentFeedback.student_id == student.id,
            StudentFeedback.parent_id == None
        )
    )
    results = feedbacks.all()
    
    # Mapping:
    # - 'answered', 'resolved', 'replied' -> answered
    # - 'closed' -> closed
    # - everything else (pending, assigned_*, processing) -> pending
    answered_statuses = ['answered', 'resolved', 'replied']
    stats = AppealStatsSchema(
        pending=len([f for f in results if f.status not in answered_statuses + ['closed', 'rejected']]),
        answered=len([f for f in results if f.status in answered_statuses]),
        closed=len([f for f in results if f.status == 'closed'])
    )
    return stats

@router.get("/{id}", response_model=FeedbackDetailSchema)
async def get_feedback_detail(
    id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG API: get_feedback_detail(id={id}, student_id={student.id})")
    """
    Get detailed conversation thread.
    Includes:
    - The Main Appeal (Student)
    - Staff Replies (FeedbackReply)
    - Student Follow-up Replies (Child StudentFeedback)
    """
    # Load separate queries for better control or specific loading
    # 1. Fetch Root
    stmt = (
        select(StudentFeedback)
        .where(StudentFeedback.id == id, StudentFeedback.student_id == student.id)
        .options(selectinload(StudentFeedback.replies), selectinload(StudentFeedback.children))
    )
    appeal = await db.scalar(stmt)
    
    if not appeal:
        logger.warning(f"DEBUG API: Appeal {id} NOT FOUND for student {student.id}")
        raise HTTPException(status_code=404, detail="Appeal not found")
    
    logger.info(f"DEBUG API: Found appeal {appeal.id}, status={appeal.status}")

    messages = []
    
    # 1. Root Message (Me)
    messages.append({
        "id": appeal.id,
        "sender": "me",
        "text": appeal.text,
        "time": (appeal.created_at.strftime("%H:%M") if appeal.created_at else "--:--"),
        "timestamp": appeal.created_at or datetime.utcnow(),
        "file_id": appeal.file_id
    })
    
    # 2. Staff Replies
    try:
        replies = appeal.replies or []
        for reply in replies:
            messages.append({
                "id": reply.id,
                "sender": "staff",
                "text": reply.text or "[Fayl]",
                "time": (reply.created_at.strftime("%H:%M") if reply.created_at else "--:--"),
                "timestamp": reply.created_at or datetime.utcnow(),
                "file_id": reply.file_id
            })
    except Exception as e:
        logger.error(f"Error processing replies for appeal {appeal.id}: {e}")
        
    # 3. Student Follow-ups (Children)
    try:
        children = appeal.children or []
        for child in children:
             messages.append({
                "id": child.id,
                "sender": "me",
                "text": child.text,
                "time": (child.created_at.strftime("%H:%M") if child.created_at else "--:--"),
                "timestamp": child.created_at or datetime.utcnow(),
                "file_id": child.file_id
            })
    except Exception as e:
        logger.error(f"Error processing children for appeal {appeal.id}: {e}")

    # Sort by time
    messages.sort(key=lambda x: x['timestamp'])

    # Map Internal Role to Display Category
    role_map = {
        "rektor": "Rahbariyat",
        "prorektor": "Rahbariyat",
        "yoshlar_prorektor": "Rahbariyat",
        "rahbariyat": "Rahbariyat",
        "dekan": "Dekanat",
        "dekan_orinbosari": "Dekanat",
        "dekan_yoshlar": "Dekanat",
        "dekanat": "Dekanat",
        "tyutor": "Tyutor",
        "psixolog": "Psixolog",
        "inspektor": "Inspektor",
        "kutubxona": "Kutubxona"
    }
    raw_role = appeal.assigned_role.lower() if appeal.assigned_role else ""
    mapped_recipient = role_map.get(raw_role, raw_role.capitalize() or "General")

    return {
        "id": appeal.id,
        "title": f"Murojaat #{appeal.id}", 
        "recipient": mapped_recipient,
        "status": appeal.status,
        "date": appeal.created_at.strftime("%d.%m.%Y"),
        "is_anonymous": appeal.is_anonymous,
        "messages": [MessageSchema(**m) for m in messages]
    }

class InitFeedbackRequest(BaseModel):
    session_id: str
    text: str
    role: str = "dekanat"
    is_anonymous: bool = False

@router.post("/init-upload")
async def initiate_feedback_upload(
    req: InitFeedbackRequest = Body(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Triggers a prompt in the Telegram bot for the user to upload a file for their appeal."""
    
    # 1. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    
    if not tg_account:
        return {"success": False, "message": "Telegram hisob ulanmagan! Avval botga kiring (@talabahamkorbot)"}
        
    # 2. Create Pending Upload Session
    session_id = req.session_id
    
    # Cleanup old pending for same session if exists
    await db.delete(await db.get(PendingUpload, session_id)) if await db.get(PendingUpload, session_id) else None
    
    new_pending = PendingUpload(
        session_id=session_id,
        student_id=student.id,
        category="feedback",
        title=req.text[:50] + "..." if len(req.text) > 50 else req.text,
        file_ids=""
    )
    db.add(new_pending)
    await db.commit()
    
    # 3. Notify Bot & Set State
    try:
        text = (
            f"📨 <b>Murojaat uchun fayl yuklash</b>\n\n"
            f"Murojaat matni: <i>{req.text}</i>\n\n"
            "<b>Iltimos, ilova qilmoqchi bo'lgan faylingizni (Rasm, Video yoki PDF) yuboring:</b>"
        )
        
        await bot.send_message(tg_account.telegram_id, text, parse_mode="HTML")
        
        # [CRITICAL] Set Bot State
        await set_bot_state(tg_account.telegram_id, FeedbackStates.WAIT_FOR_APP_FILE)
        
        return {"success": True, "message": "Botga yuklash so'rovi yuborildi. Telegramni oching.", "session_id": session_id}
    except Exception as e:
        return {"success": False, "message": f"Botga xabar yuborishda xatolik: {str(e)}"}

@router.get("/upload-status/{session_id}")
async def check_feedback_upload_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Check if file has been uploaded for this feedback session."""
    pending = await db.get(PendingUpload, session_id)
    
    if not pending:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if pending.file_ids:
        file_id = pending.file_ids.split(",")[0]
        return {
            "status": "uploaded", 
            "file_id": file_id
        }
    
    return {"status": "pending"}

@router.post("")
async def create_feedback(
    text: str = Form(...),
    role: str = Form("dekanat"), 
    is_anonymous: bool = Form(False),
    session_id: Optional[str] = Form(None), # For Telegram-upload flow
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Send feedback/appeal to specific staff role.
    """
    
    feedback = StudentFeedback(
        student_id=student.id,
        text=text,
        assigned_role=role,
        is_anonymous=is_anonymous,
        status="pending",
        # Snapshot Data
        student_full_name=student.full_name,
        student_group=student.group_number,
        student_faculty=student.faculty_name,
        student_phone=student.phone
    )
    
    if session_id:
        pending = await db.get(PendingUpload, session_id)
        if pending and pending.file_ids:
            feedback.file_id = pending.file_ids.split(",")[0]
            feedback.file_type = "document" # Simplification
            await db.delete(pending)

    db.add(feedback)
    await db.commit()
    return {"status": "success", "id": feedback.id}

@router.post("/{id}/reply")
async def reply_feedback(
    id: int,
    text: str = Form(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Reply to an existing feedback thread.
    Creates a new StudentFeedback with parent_id = id.
    """
    # Verify parent exists and belongs to student
    parent = await db.scalar(select(StudentFeedback).where(StudentFeedback.id == id, StudentFeedback.student_id == student.id))
    if not parent:
         raise HTTPException(status_code=404, detail="Appeal not found")
         
    reply = StudentFeedback(
        student_id=student.id,
        text=text,
        assigned_role=parent.assigned_role,
        is_anonymous=parent.is_anonymous,
        status="pending",
        parent_id=parent.id, # Link to parent
        # Snapshot Data
        student_full_name=student.full_name,
        student_group=student.group_number,
        student_faculty=student.faculty_name,
        student_phone=student.phone
    )
    
    db.add(reply)
    await db.commit()
    
    return {"status": "success", "id": reply.id}

@router.post("/{id}/close")
async def close_feedback(
    id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Close a feedback thread.
    """
    stmt = select(StudentFeedback).where(StudentFeedback.id == id, StudentFeedback.student_id == student.id)
    appeal = await db.scalar(stmt)
    
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
        
    appeal.status = "closed"
    await db.commit()
    
    return {"status": "success", "message": "Appeal closed"}

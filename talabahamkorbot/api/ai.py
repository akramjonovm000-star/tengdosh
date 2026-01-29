from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from services.ai_service import generate_response
from database.models import Student, AiMessage
from database.db_connect import get_session
from api.dependencies import get_current_student, get_premium_student

router = APIRouter(prefix="/ai", tags=["ai"])

class ChatRequest(BaseModel):
    message: str

@router.get("/history")
async def get_chat_history(
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_session)
):
    """
    Get chat history for current student.
    """
    stmt = select(AiMessage).where(AiMessage.student_id == student.id).order_by(AiMessage.created_at)
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} 
            for m in messages
        ]
    }

@router.delete("/history")
async def clear_chat_history(
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_session)
):
    """
    Clear all chat history.
    """
    stmt = delete(AiMessage).where(AiMessage.student_id == student.id)
    await db.execute(stmt)
    await db.commit()
    
    return {"success": True, "message": "Tarix tozalandi"}

@router.post("/chat")
async def chat_with_ai(
    req: ChatRequest,
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_session)
):
    """
    AI Chat endpoint with persistence.
    """
    if not req.message:
        return {"success": False, "message": "Bo'sh xabar"}
        
    # 1. Save User Message
    user_msg = AiMessage(student_id=student.id, role="user", content=req.message)
    db.add(user_msg)
    await db.commit()
        
    # 2. Generate Response
    # Context Injection
    context = (
        f"Talaba ma'lumotlari:\n"
        f"Ism: {student.full_name}\n"
        f"Universitet: {student.university_name or 'Noma`lum'}\n"
        f"Fakultet: {student.faculty_name or 'Noma`lum'}\n"
        f"Yo'nalish: {student.specialty_name or 'Noma`lum'}\n"
        f"Bosqich: {student.level_name or ''} ({student.semester_name or ''})\n"
        f"Ta'lim shakli: {student.payment_form or 'Noma`lum'} (Moliya turi)\n"
    )
    
    full_prompt = f"Context:\n{context}\n\nSavol: {req.message}"
    
    response_text = await generate_response(full_prompt)
    
    # 3. Save AI Response
    ai_msg = AiMessage(student_id=student.id, role="assistant", content=response_text)
    db.add(ai_msg)
    await db.commit()
    
    return {"success": True, "data": response_text}


from fastapi import UploadFile, File, Form, HTTPException
import shutil
import os
import time
from services.ai_service import summarize_konspekt
from utils.document_parser import extract_text_from_file

@router.post("/summarize")
async def summarize_content(
    file: UploadFile = File(None),
    text: str = Form(None),
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_session)
):
    """
    Generate a summary (konspekt) from a file or text.
    Processed completely in-memory (no disk write).
    """
    # --- LIMIT CHECK ---
    # Monthly Reset Logic
    now_utc = datetime.utcnow()
    if student.ai_last_reset:
        if student.ai_last_reset.month != now_utc.month or student.ai_last_reset.year != now_utc.year:
            student.ai_usage_count = 0
            student.ai_last_reset = now_utc
            # Ensure proper limit for paid users if somehow lost, or just trust stored limit
    else:
        student.ai_last_reset = now_utc

    # Check limit (Default 25 if not set)
    limit = student.ai_limit if student.ai_limit is not None else 25
    
    # If admin/owner -> Unlimited
    if student.role == 'owner':
        limit = 9999
        
    if student.ai_usage_count >= limit:
        msg = "Bu oy uchun limitlar ishlatib bo'lingan."
        if limit <= 5: # Trial
             msg = "Sinov davri uchun ajratilgan limit tugadi (5 ta)."
             
        return {
            "success": False,
            "message": msg
        }
    # -------------------

    content_to_summarize = ""

    # 1. Handle File (Stream)
    if file:
        try:
            file_ext = file.filename.split(".")[-1]
            
            # Use the SpooledTemporaryFile directly without saving to disk
            from utils.document_parser import extract_text_from_stream
            content_to_summarize = extract_text_from_stream(file.file, file_ext)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Faylni o'qishda xatolik: {str(e)}")

    # 2. Handle Text (fallback)
    elif text:
        content_to_summarize = text

    # 3. Validate
    msg = content_to_summarize.strip()
    if not msg or len(msg) < 10:
         return {
             "success": False, 
             "message": "Matn juda qisqa yoki o'qib bo'lmadi. Iltimos, boshqa fayl/matn yuboring."
         }

    # 4. Generate Summary
    try:
        summary = await summarize_konspekt(msg)
        
        # Increment Usage
        student.ai_usage_count += 1
        await db.commit()
        
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "message": f"AI xatolik: {str(e)}"}

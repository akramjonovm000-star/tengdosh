from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from services.ai_service import generate_response, generate_answer_by_key
from services.analytics_service import get_ai_analytics_summary
from services.context_builder import build_student_context
from services.grant_service import calculate_grant_score
from services.hemis_service import HemisService
from database.models import Student, AiMessage
from database.db_connect import get_session
from api.dependencies import get_current_student, get_premium_student
from config import OPENAI_MODEL_CHAT, OPENAI_MODEL_OWNER, ADMIN_ACCESS_ID

router = APIRouter(tags=["ai"])

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

    # 2. Student Background Context & Personalization
    name_parts = student.full_name.split()
    # User said: "familiya, ism, sharif ketma ketligida", so ism is 2nd part (index 1)
    first_name = name_parts[1] if len(name_parts) > 1 else name_parts[0]

    context = (
        f"Talaba ma'lumotlari:\n"
        f"Ism: {student.full_name}\n"
        f"Universitet: {student.university_name or 'Noma`lum'}\n"
        f"Fakultet: {student.faculty_name or 'Noma`lum'}\n"
        f"Yo'nalish: {student.specialty_name or 'Noma`lum'}\n"
        f"Bosqich: {student.level_name or ''} ({student.semester_name or ''})\n"
        f"Ta'lim shakli: {student.payment_form or 'Noma`lum'} (Moliya turi)\n"
    )
    
    # Add AI Context if available (contains subjects, grades, etc.)
    context_str = student.ai_context
    need_update = False
    if not context_str:
        need_update = True
    elif student.last_context_update:
        if datetime.utcnow() - student.last_context_update > timedelta(hours=24):
            need_update = True
            
    if need_update:
        try:
            context_str = await build_student_context(db, student.id)
        except Exception as e:
            # logging already done in builder
            pass
            
    if context_str:
        context += f"\n\nBATAFSIL MA'LUMOTLAR (Akademik):\n{context_str}"

    # 3. Fetch Recent History for Context
    hist_stmt = select(AiMessage).where(AiMessage.student_id == student.id).order_by(AiMessage.created_at.desc()).limit(6)
    hist_res = await db.execute(hist_stmt)
    recent_msgs = hist_res.scalars().all()
    # Skip the one we just saved for history context but include others
    recent_msgs = recent_msgs[1:] 
    recent_msgs.reverse() # Back to chronological
    
    history_context = ""
    if recent_msgs:
        history_context = "Oxirgi xabarlar:\n" + "\n".join([f"{'Siz' if m.role == 'user' else 'AI'}: {m.content}" for m in recent_msgs])

    full_prompt = f"Context:\n{context}\n\n{history_context}\n\nYangi savol: {req.message}"
    
    # Check for Elevated Access (Owner or Specific Admin)
    is_admin = False
    if getattr(student, 'role', None) == 'owner':
        is_admin = True
    elif getattr(student, 'hemis_id', None) == ADMIN_ACCESS_ID or getattr(student, 'hemis_login', None) == ADMIN_ACCESS_ID:
        is_admin = True
        
    model = OPENAI_MODEL_CHAT
    system_context = None
    
    if is_admin:
        model = OPENAI_MODEL_OWNER
        # Inject DB Analytics
        system_context = await get_ai_analytics_summary(db)
    
    # Non-streaming response for mobile app compatibility
    full_response = await generate_response(
        full_prompt, 
        model=model, 
        stream=False, 
        system_context=system_context,
        role="owner" if is_admin else getattr(student, 'role', 'student'),
        user_name=first_name
    )
    
    # Save Assistant Message
    ai_msg = AiMessage(student_id=student.id, role="assistant", content=full_response)
    db.add(ai_msg)
    await db.commit()
    
    return {"success": True, "data": full_response}


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
    if getattr(student, 'role', None) == 'owner':
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

@router.post("/predict-grant")
async def predict_grant_analysis(
    student: Student = Depends(get_premium_student),
    db: AsyncSession = Depends(get_session)
):
    """
    Personalized AI Grant Analysis (Mirroring Telegram Bot).
    """
    try:
        # 1. Fetch Latest Data & Calculate Stats
        hemis_service = HemisService()
        stats = await calculate_grant_score(student, db, hemis_service)
        
        # 2. Build Detailed Prompt
        prompt = (
            f"Talaba ismi: {student.full_name}\n"
            f"GPA: {stats['gpa']} (Maksimum 5.0)\n"
            f"Akademik Ball (GPA x 16): {stats['academic_score']} / 80\n"
            f"Ijtimoiy Faollik Ball (Raw/5): {stats['social_score']} / 20\n"
            f"YAKUNIY BALL: {stats['total_score']} / 100\n\n"
            "FAOLLIKLAR TABLE BO'YICHA HOLAT:\n"
        )
        
        cat_names = {
            "togarak": "To'garaklar (5 tashabbus)",
            "yutuqlar": "Yutuqlar (Olimpiada/Sport)",
            "marifat": "Ma'rifat darslari",
            "volontyorlik": "Volontyorlik",
            "madaniy": "Madaniy tashriflar",
            "sport": "Sport",
            "boshqa": "Boshqa"
        }
        
        for detail in stats['details']:
            cat_key = detail['category']
            name = cat_names.get(cat_key, cat_key.capitalize())
            prompt += f"- {name}: {detail['count']} ta tasdiqlangan. Berilgan ball: {round(detail['earned'], 1)} (Max {detail['max_points']})\n"
            
        prompt += """
        
        SENING VAZIFANG:
        Yuqoridagi ma'lumotlar asosida talabaga Grant olish imkoniyatini "Grant Taqsimoti va Reglamenti" asosida tushuntirib berish.
        
        ⚠️ QOIDALAR:
        1. Murojaat: "Hurmatli talaba" deb murojaat qil.
        2. Ohang: Muloyim, lekin kuchli motivatsiya beruvchi. Rasmiyatchilik kamroq bo'lsin.
        3. Hech qachon "Aniq olasiz" dema. "Taxminiy", "Imkoniyat yuqori/past" deb ayt.
        4. Javob strukturasi:
           - 🎯 Taxminiy ball (Jami xx / 100)
           - 📘 Akademik (GPA) hissasi
           - 🤝 Ijtimoiy faollik hissasi
           - 🔥 Motivatsiya va Harakatga chaqiruv
           - 💡 Aniq Reja (Action Plan)
        """
        
        # 3. Generate AI Response
        ai_response = await generate_answer_by_key("grant_calc", prompt)
        
        if not ai_response:
             return {"success": False, "message": "AI javob bera olmadi."}

        # 4. Save History (Optional but good for consistency)
        ai_msg = AiMessage(student_id=student.id, role="assistant", content=ai_response)
        db.add(ai_msg)
        await db.commit()
        
        return {"success": True, "data": ai_response}
        
    except Exception as e:
        await db.rollback()
        return {"success": False, "message": f"Xatolik: {str(e)}"}

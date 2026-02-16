from fastapi import APIRouter, Depends, HTTPException, Body, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Student, TgAccount, StudentDocument, PendingUpload
from database.db_connect import get_session
from api.dependencies import get_current_student
from services.hemis_service import HemisService
from bot import bot
from aiogram.types import BufferedInputFile

# [SECURITY] Import Limiter
from api.security import limiter

router = APIRouter(tags=["Documents"])

class DocumentRequest(BaseModel):
    type: str # 'reference', 'transcript', 'contract'

@router.get("")
async def get_my_documents(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Returns real documents uploaded by the student or for the student"""
    stmt = select(StudentDocument).where(
        StudentDocument.student_id == student.id,
        StudentDocument.file_type == "document",
        StudentDocument.is_active == True # [SECURITY] Soft Delete Filter
    ).order_by(StudentDocument.uploaded_at.desc())
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": d.id,
                "title": d.file_name,
                "type": d.file_type,
                "created_at": d.uploaded_at.strftime("%d.%m.%Y")
            } for d in docs
        ]
    }

# ... (Previous code omitted for brevity) ...

@router.delete("/{doc_id}")
@limiter.limit("5/minute")
async def delete_document(
    request: Request, # Required for limiter
    doc_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Deletes a student's document (Soft Delete)"""
    stmt = select(StudentDocument).where(StudentDocument.id == doc_id, StudentDocument.student_id == student.id)
    result = await db.execute(stmt)
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
        
    # [SECURITY] Soft Delete instead of Hard Delete
    doc.is_active = False
    await db.commit()
    
    return {"success": True, "message": "Hujjat muvaffaqiyatli o'chirildi"}

from models.states import DocumentAddStates
from aiogram.fsm.storage.base import StorageKey

async def set_bot_state(user_id: int, state):
    from bot import dp, bot
    from config import BOT_TOKEN
    
    bot_id = bot.id
    if bot_id is None:
        try:
            bot_id = int(BOT_TOKEN.split(":")[0])
        except:
            print("Failed to derive bot_id from token")
            
    key = StorageKey(bot_id=bot_id, chat_id=user_id, user_id=user_id)
    # Convert state object to string if needed
    state_str = state.state if hasattr(state, "state") else str(state)
    await dp.storage.set_state(key, state_str)

class InitUploadRequest(BaseModel):
    session_id: str # UUID from App
    category: str | None = None
    title: str | None = None

@router.post("/init-upload")
async def initiate_document_upload(
    req: InitUploadRequest = Body(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Triggers a prompt in the Telegram bot for the user to upload a document"""
    from database.models import PendingUpload, TgAccount, SecurityToken
    from services.token_service import TokenService
    from config import BOT_USERNAME
    
    # 1. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    
    # [SMART CONTEXT] Logic
    if not tg_account:
        # Generate Auth Token for Deep Link
        # We can use a short-lived token or just sign the student_id
        # Let's use a simple signed format: auth_<student_id>_<timestamp>_signature
        # OR just reuse the ATS system if appropriate, but ATS is for actions.
        # Let's keep it simple: "auth_{student_id}" is insecure if guessed.
        # Better: Generate a specialized token.
        
        # New approach: Use PendingUpload session_id as the auth token!
        # When user clicks start=session_id, we link them AND set state.
        
        auth_link = f"https://t.me/{BOT_USERNAME}?start=upload_{req.session_id}"
        
        # Create PendingUpload even if not linked, so we can link later
        # Parse Intent
        category = req.category if req.category else "boshqa"
        title = req.title if req.title else "Hujjat"
        
        # Cleanup old pending for same session
        existing = await db.get(PendingUpload, req.session_id)
        if existing: await db.delete(existing)
        
        new_pending = PendingUpload(
            session_id=req.session_id,
            student_id=student.id,
            category=category,
            title=title,
            file_ids=""
        )
        db.add(new_pending)
        await db.commit()

        return {
            "success": False, 
            "requires_auth": True, 
            "auth_link": auth_link,
            "message": "Telegram hisob ulanmagan. Iltimos, havolani oching."
        }
        
    # 2. Existing Account Logic (Smart Flow)
    session_id = req.session_id
    
    # Cleanup old pending
    existing = await db.get(PendingUpload, session_id)
    if existing: await db.delete(existing)
    
    category = req.category if req.category else "boshqa"
    title = req.title if req.title else "Hujjat"
    
    new_pending = PendingUpload(
        session_id=session_id,
        student_id=student.id,
        category=category,
        title=title,
        file_ids=""
    )
    db.add(new_pending)
    await db.commit()
    
    # 3. Notify Bot & Set State
    try:
        display_name = title if title else (category if category else "Hujjat")
        
        text = (
            f"📎 <b>Hujjat yuklash: {display_name}</b>\n\n"
            f"Ilovadan '{display_name}' hujjatini yuklash so'rovini yubordingiz. "
            "<b>Iltimos, faylni (PDF, rasm yoki DOC) shunchaki yuboring:</b>"
        )
        
        await bot.send_message(tg_account.telegram_id, text, parse_mode="HTML")
        
        # [CRITICAL] Set Bot State
        await set_bot_state(tg_account.telegram_id, DocumentAddStates.WAIT_FOR_APP_FILE)
        
        return {
            "success": True, 
            "requires_auth": False,
            "message": "Botga yuklash so'rovi yuborildi. Telegramni oching.", 
            "session_id": session_id,
            "bot_link": f"https://t.me/{BOT_USERNAME}"
        }
    except Exception as e:
        return {"success": False, "message": f"Botga xabar yuborishda xatolik: {str(e)}"}

@router.get("/upload-status/{session_id}")
async def check_upload_status(
    session_id: str,
    db: AsyncSession = Depends(get_session)
):
    """Check if file has been uploaded for this session."""
    from database.models import PendingUpload
    pending = await db.get(PendingUpload, session_id)
    
    if not pending:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if pending.file_ids:
        # We assume only one file for document upload for now
        file_id = pending.file_ids.split(",")[0]
        # We also need to know if it was a photo or document
        # Let's check the type if we saved it... 
        # Actually PendingUpload doesn't have file_type, we might need it.
        # For now, let's just return file_ids
        return {
            "status": "uploaded", 
            "file_id": file_id
        }
    
    return {"status": "pending"}

from api.dependencies import get_current_student, require_action_token

@router.post("/finalize")
async def finalize_upload(
    session_id: str = Body(..., embed=True),
    token: str = Depends(require_action_token), # [SECURITY] ATS Enforced
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Saves the uploaded file from PendingUpload to StudentDocument"""
    pending = await db.get(PendingUpload, session_id)
    
    if not pending or not pending.file_ids:
        raise HTTPException(status_code=400, detail="Fayl hali yuklanmagan")
        
    # [SECURITY] Verify Ownership
    if pending.student_id != student.id:
        raise HTTPException(status_code=403, detail="Siz faqat o'zingiz yuklagan faylni saqlay olasiz")

    file_id = pending.file_ids.split(",")[0]
    
    # Create Real Document
    doc = StudentDocument(
        student_id=student.id,
        file_name=pending.title or "Hujjat",
        telegram_file_id=file_id,
        telegram_file_unique_id=pending.file_unique_id,
        file_size=pending.file_size,
        mime_type=pending.mime_type,
        file_type="document",
        uploaded_by="student",
        is_active=True
    )
    db.add(doc)
    
    # Cleanup pending
    await db.delete(pending)
    await db.commit()
    
    return {"success": True, "message": "Hujjat muvaffaqiyatli saqlandi!"}

@router.post("/{doc_id}/send-to-bot")
async def send_existing_doc_to_bot(
    doc_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Sends a previously uploaded document to the student's Telegram"""
    # 1. Get Document
    stmt = select(StudentDocument).where(StudentDocument.id == doc_id, StudentDocument.student_id == student.id)
    result = await db.execute(stmt)
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
        
    # 2. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    
    if not tg_account:
        return {"success": False, "message": "Telegram hisob ulanmagan."}
        
    # 3. Send via Bot
    try:
        caption = f"📄 <b>{doc.file_name}</b>"
        # Determine send method
        is_photo = doc.mime_type and "image" in doc.mime_type
        
        if is_photo:
            await bot.send_photo(tg_account.telegram_id, doc.telegram_file_id, caption=caption, parse_mode="HTML")
        else:
            await bot.send_document(tg_account.telegram_id, doc.telegram_file_id, caption=caption, parse_mode="HTML")
            
        return {"success": True, "message": "Hujjat Telegramingizga yuborildi!"}
    except Exception as e:
        logger.error(f"Error sending doc to bot: {e}")
        return {"success": False, "message": f"Botda xatolik: {str(e)}"}

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Deletes a student's document"""
    stmt = select(StudentDocument).where(StudentDocument.id == doc_id, StudentDocument.student_id == student.id)
    result = await db.execute(stmt)
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Hujjat topilmadi")
        
    await db.delete(doc)
    await db.commit()
    
    return {"success": True, "message": "Hujjat muvaffaqiyatli o'chirildi"}
@router.post("/send")
async def send_hemis_document(
    req: DocumentRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Handles generation and sending of official HEMIS documents (Reference, Transcript, etc.)"""
    # 1. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    if not tg_account: 
        return {"success": False, "message": "Botga ulanmagansiz."}
    
    chat_id = tg_account.telegram_id
    doc_type = req.type.lower()
    
    # 2. Handle Reference
    if "reference" in doc_type or "ma'lumotnoma" in doc_type:
        # User requested to disable PDF service
        return {"success": False, "message": "Ushbu xizmat vaqtincha o'chirilgan."}

    # 3. Handle Transcript
    if "transcript" in doc_type or "transkript" in doc_type:
         # User requested to disable PDF service
        return {"success": False, "message": "Ushbu xizmat vaqtincha o'chirilgan."}

    # 4. Handle Study Sheet
    if "study" in doc_type or "uquv" in doc_type or "o'quv" in doc_type:
         # User requested to disable PDF service
        return {"success": False, "message": "Ushbu xizmat vaqtincha o'chirilgan."}

    # 5. Handle Contract
    if "contract" in doc_type or "shartnoma" in doc_type:
        message = (
            f"📄 <b>To'lov-kontrakt shartnomasi</b>\n\n"
            f"Hurmatli {student.full_name}, shartnomani yuklab olish uchun bosing:\n\n"
            f"🔗 <a href='https://student.jmcu.uz/finance/contract_pdf'>Yuklab olish (PDF)</a>"
        )
        await bot.send_message(chat_id, message, parse_mode="HTML")
        return {"success": True, "message": "Shartnoma havolasi Telegramga yuborildi"}

    return {"success": False, "message": "Noma'lum hujjat turi"}
from typing import List
from pydantic import BaseModel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

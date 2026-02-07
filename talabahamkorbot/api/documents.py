from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Student, TgAccount
from database.db_connect import get_session
from api.dependencies import get_current_student
from services.hemis_service import HemisService
from bot import bot
from aiogram.types import BufferedInputFile

router = APIRouter(tags=["Documents"])

class DocumentRequest(BaseModel):
    type: str # 'reference', 'transcript', 'contract'

@router.get("")
async def get_my_documents(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Returns real documents uploaded by the student or for the student"""
    from database.models import UserDocument
    stmt = select(UserDocument).where(UserDocument.student_id == student.id).order_by(UserDocument.created_at.desc())
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": d.id,
                "title": d.title,
                "category": d.category,
                "type": d.file_type,
                "status": d.status,
                "created_at": d.created_at.strftime("%d.%m.%Y")
            } for d in docs
        ]
    }

from models.states import DocumentAddStates
from aiogram.fsm.storage.base import StorageKey

async def set_bot_state(user_id: int, state):
    from bot import dp, bot
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    await dp.storage.set_state(key, state)

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
    from database.models import PendingUpload, TgAccount
    
    # 1. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    
    if not tg_account:
        return {"success": False, "message": "Telegram hisob ulanmagan! Avval botga kiring (@talabahamkorbot)"}
        
    # 2. Create Session
    session_id = req.session_id
    
    # Cleanup old pending for same session if exists
    await db.delete(await db.get(PendingUpload, session_id)) if await db.get(PendingUpload, session_id) else None
    
    # Parse Intent
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
        
        return {"success": True, "message": "Botga yuklash so'rovi yuborildi. Telegramni oching.", "session_id": session_id}
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

@router.post("/finalize")
async def finalize_upload(
    session_id: str = Body(..., embed=True),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Saves the uploaded file from PendingUpload to UserDocument"""
    from database.models import PendingUpload, UserDocument
    pending = await db.get(PendingUpload, session_id)
    
    if not pending or not pending.file_ids:
        raise HTTPException(status_code=400, detail="Fayl hali yuklanmagan")
        
    file_id = pending.file_ids.split(",")[0]
    
    # Create Real Document
    doc = UserDocument(
        student_id=student.id,
        category=pending.category or "Shaxsiy",
        title=pending.title or "Hujjat",
        description="Ilovadan yuklangan",
        file_id=file_id,
        file_type="document", # Default, can be refined if we store type in PendingUpload
        status="active"
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
    from database.models import UserDocument, TgAccount
    
    # 1. Get Document
    stmt = select(UserDocument).where(UserDocument.id == doc_id, UserDocument.student_id == student.id)
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
        caption = f"📄 <b>{doc.title}</b>\nKategoriya: {doc.category}"
        if doc.file_type == "photo":
            await bot.send_photo(tg_account.telegram_id, doc.file_id, caption=caption, parse_mode="HTML")
        else:
            await bot.send_document(tg_account.telegram_id, doc.file_id, caption=caption, parse_mode="HTML")
            
        return {"success": True, "message": "Hujjat Telegramingizga yuborildi!"}
    except Exception as e:
        return {"success": False, "message": f"Botda xatolik: {str(e)}"}

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Deletes a student's document"""
    from database.models import UserDocument
    stmt = select(UserDocument).where(UserDocument.id == doc_id, UserDocument.student_id == student.id)
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

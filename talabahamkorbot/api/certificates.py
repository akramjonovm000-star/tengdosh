from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from pydantic import BaseModel
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)

from api.dependencies import get_current_student
from database.db_connect import get_session
from database.models import Student, StudentDocument, TgAccount, PendingUpload
from bot import bot

router = APIRouter(tags=["Certificates"])

@router.get("")
async def get_my_certificates(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Returns real certificates uploaded by/for the student"""
    stmt = select(StudentDocument).where(
        StudentDocument.student_id == student.id,
        StudentDocument.file_type == "certificate"
    ).order_by(StudentDocument.uploaded_at.desc())
    result = await db.execute(stmt)
    certs = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": c.id,
                "title": c.file_name,
                "file_id": c.telegram_file_id,
                "created_at": c.uploaded_at.strftime("%d.%m.%Y")
            } for c in certs
        ]
    }

from models.states import CertificateAddStates
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

class InitCertRequest(BaseModel):
    session_id: str
    category: str | None = None
    title: str | None = None

@router.post("/init-upload")
async def initiate_certificate_upload(
    req: InitCertRequest = Body(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Triggers a prompt in the Telegram bot for the user to upload a certificate"""
    
    # 1. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    
    if not tg_account:
        return {"success": False, "message": "Telegram hisob ulanmagan! Avval botga kiring (@talabahamkorbot)"}
        
    # 2. Create Session
    session_id = req.session_id
    # Default values for certificate
    category = "sertifikat" 
    title = req.title if req.title else "Sertifikat"
    
    # Cleanup old pending for same session if exists
    await db.delete(await db.get(PendingUpload, session_id)) if await db.get(PendingUpload, session_id) else None
    
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
        text = (
            f"🎓 <b>Sertifikat yuklash: {title}</b>\n\n"
            f"Ilovadan '{title}' sertifikatini yuklash so'rovini yubordingiz. "
            "<b>Iltimos, sertifikat faylini (PDF yoki rasm) shunchaki yuboring:</b>"
        )
        
        await bot.send_message(tg_account.telegram_id, text, parse_mode="HTML")
        
        # [CRITICAL] Set Bot State
        await set_bot_state(tg_account.telegram_id, CertificateAddStates.WAIT_FOR_APP_FILE)
        
        return {"success": True, "message": "Botga yuklash so'rovi yuborildi. Telegramni oching.", "session_id": session_id}
    except Exception as e:
        return {"success": False, "message": f"Botga xabar yuborishda xatolik: {str(e)}"}

@router.get("/upload-status/{session_id}")
async def check_cert_upload_status(
    session_id: str,
    db: AsyncSession = Depends(get_session)
):
    """Check if file has been uploaded for this certificate session."""
    from database.models import PendingUpload
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

from api.dependencies import get_current_student, require_action_token

@router.post("/finalize")
async def finalize_certificate_upload(
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
    
    # Create Real Certificate
    cert = StudentDocument(
        student_id=student.id,
        file_name=pending.title or "Sertifikat",
        telegram_file_id=file_id,
        telegram_file_unique_id=pending.file_unique_id,
        file_size=pending.file_size,
        mime_type=pending.mime_type,
        file_type="certificate",
        uploaded_by="student",
        is_active=True
    )
    db.add(cert)
    
    # Cleanup pending
    await db.delete(pending)
    await db.commit()
    
    return {"success": True, "message": "Sertifikat muvaffaqiyatli saqlandi!"}

@router.post("/{cert_id}/send-to-bot")
async def send_cert_to_bot(
    cert_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Sends a stored certificate to the student's Telegram"""
    # 1. Get Cert
    stmt = select(StudentDocument).where(StudentDocument.id == cert_id, StudentDocument.student_id == student.id)
    result = await db.execute(stmt)
    cert = result.scalars().first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Sertifikat topilmadi")
        
    # 2. Check TG Account
    stmt = select(TgAccount).where(TgAccount.student_id == student.id)
    result = await db.execute(stmt)
    tg_account = result.scalars().first()
    
    if not tg_account:
        return {"success": False, "message": "Telegram hisob ulanmagan."}
        
    # 3. Send via Bot
    try:
        caption = f"🎓 <b>{cert.file_name}</b>"
        # Determine send method
        is_photo = cert.mime_type and "image" in cert.mime_type
        
        if is_photo:
            await bot.send_photo(tg_account.telegram_id, cert.telegram_file_id, caption=caption, parse_mode="HTML")
        else:
            await bot.send_document(tg_account.telegram_id, cert.telegram_file_id, caption=caption, parse_mode="HTML")
                
        return {"success": True, "message": "Sertifikat Telegramingizga yuborildi!"}
    except Exception as e:
        logger.error(f"Error sending cert to bot: {e}")
        return {"success": False, "message": f"Botda xatolik: {str(e)}"}

@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Deletes a student's certificate"""
    stmt = select(StudentDocument).where(StudentDocument.id == cert_id, StudentDocument.student_id == student.id)
    result = await db.execute(stmt)
    cert = result.scalars().first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Sertifikat topilmadi")
        
    await db.delete(cert)
    await db.commit()
    
    return {"success": True, "message": "Sertifikat muvaffaqiyatli o'chirildi"}

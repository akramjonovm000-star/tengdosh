from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from pydantic import BaseModel
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from api.dependencies import get_current_student
from database.db_connect import get_session
from database.models import Student, UserCertificate, TgAccount, PendingUpload
from bot import bot

router = APIRouter(prefix="/student/certificates", tags=["Certificates"])

@router.get("")
async def get_my_certificates(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Returns real certificates uploaded by/for the student"""
    stmt = select(UserCertificate).where(UserCertificate.student_id == student.id).order_by(UserCertificate.created_at.desc())
    result = await db.execute(stmt)
    certs = result.scalars().all()
    
    return {
        "success": True, 
        "data": [
            {
                "id": c.id,
                "title": c.title,
                "file_id": c.file_id,
                "created_at": c.created_at.strftime("%d.%m.%Y")
            } for c in certs
        ]
    }

from models.states import CertificateAddStates
from aiogram.fsm.storage.base import StorageKey

async def set_bot_state(user_id: int, state):
    from bot import dp, bot
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    await dp.storage.set_state(key, state)

class InitCertRequest(BaseModel):
    session_id: str
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
    title = req.title if req.title else "Sertifikat"
    
    # Cleanup old pending for same session if exists
    await db.delete(await db.get(PendingUpload, session_id)) if await db.get(PendingUpload, session_id) else None
    
    new_pending = PendingUpload(
        session_id=session_id,
        student_id=student.id,
        category="sertifikat",
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

@router.post("/finalize")
async def finalize_certificate_upload(
    session_id: str = Body(..., embed=True),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Saves the uploaded file from PendingUpload to UserCertificate"""
    from database.models import PendingUpload, UserCertificate
    pending = await db.get(PendingUpload, session_id)
    
    if not pending or not pending.file_ids:
        raise HTTPException(status_code=400, detail="Fayl hali yuklanmagan")
        
    file_id = pending.file_ids.split(",")[0]
    
    # Create Real Certificate
    cert = UserCertificate(
        student_id=student.id,
        title=pending.title or "Sertifikat",
        file_id=file_id
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
    stmt = select(UserCertificate).where(UserCertificate.id == cert_id, UserCertificate.student_id == student.id)
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
        caption = f"🎓 <b>{cert.title}</b>"
        await bot.send_document(tg_account.telegram_id, cert.file_id, caption=caption, parse_mode="HTML")
        return {"success": True, "message": "Sertifikat Telegramingizga yuborildi!"}
    except Exception as e:
        return {"success": False, "message": f"Botda xatolik: {str(e)}"}

@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_session)
):
    """Deletes a student's certificate"""
    from database.models import UserCertificate
    stmt = select(UserCertificate).where(UserCertificate.id == cert_id, UserCertificate.student_id == student.id)
    result = await db.execute(stmt)
    cert = result.scalars().first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Sertifikat topilmadi")
        
    await db.delete(cert)
    await db.commit()
    
    return {"success": True, "message": "Sertifikat muvaffaqiyatli o'chirildi"}

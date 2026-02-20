from aiogram import Router, F, types
from aiogram.filters import StateFilter
from sqlalchemy import select
from database.db_connect import get_session
from database.models import PendingUpload, Student, TgAccount
from models.states import DocumentAddStates, CertificateAddStates, FeedbackStates, ActivityUploadState
from bot import bot

router = Router()

@router.message(StateFilter(DocumentAddStates.WAIT_FOR_APP_FILE, CertificateAddStates.WAIT_FOR_APP_FILE, FeedbackStates.WAIT_FOR_APP_FILE), F.document | F.photo)
async def handle_app_file_upload(message: types.Message, state):
    """
    Handles file upload when user is in WAIT_FOR_APP_FILE state.
    This state is set by the Mobile App via /api/v1/student/documents/init-upload
    """
    try:
        user_id = message.from_user.id
        
        # 1. Get File ID
        file_id = ""
        file_unique_id = ""
        file_size = 0
        mime_type = ""
        
        if message.document:
            file_id = message.document.file_id
            file_unique_id = message.document.file_unique_id
            file_size = message.document.file_size
            mime_type = message.document.mime_type or "application/octet-stream"
        elif message.photo:
            # Get largest photo
            photo = message.photo[-1]
            file_id = photo.file_id
            file_unique_id = photo.file_unique_id
            file_size = photo.file_size
            mime_type = "image/jpeg"
            
        if not file_id:
             await message.answer("❌ Fayl aniqlanmadi. Iltimos qaytadan urining.")
             return

        # 2. Find Pending Upload Session for this User
        # We need to find which student corresponds to this TG ID
        async for db in get_session():
             # Find Student via TgAccount
             stmt = select(TgAccount).where(TgAccount.telegram_id == user_id)
             result = await db.execute(stmt)
             tg_account = result.scalars().first()
             
             if not tg_account:
                 await message.answer("❌ Sizning Telegram hisobingiz talaba profiliga ulanmagan.")
                 return
                 
             # Find latest PendingUpload for this student
             # NOTE:Ideally we should have session_id in state data, but init-upload only sets state string.
             # We assume the Last Created Pending Upload is the target. 
             # Or we can check if there is *any* pending upload for this student.
             
             # Better approach: Find pending upload where file_ids is EMPTY
             stmt = select(PendingUpload).where(
                 PendingUpload.student_id == tg_account.student_id,
                 (PendingUpload.file_ids == "") | (PendingUpload.file_ids == None)
             ).order_by(PendingUpload.created_at.desc())
             
             result = await db.execute(stmt)
             pending = result.scalars().first()
             
             if not pending:
                 await message.answer("⚠️ Hujjat yuklash sessiyasi topilmadi yoki muddati tugagan. Ilovadan qayta urinib ko'ring.")
                 await state.clear()
                 return
                 
             # 3. Update Pending Upload
             pending.file_ids = file_id
             pending.file_unique_id = file_unique_id
             pending.file_size = file_size
             pending.mime_type = mime_type
             
             await db.commit()
             
             # 4. Notify User
             await message.answer(
                 f"✅ <b>{pending.title or 'Hujjat'}</b> qabul qilindi!\n\n"
                 "Endi ilovaga qaytib, <b>'Saqlash'</b> tugmasini bosing.",
                 parse_mode="HTML"
             )
             
             # 5. Clear State
             await state.clear()
             return

    except Exception as e:
        print(f"Error in handle_app_file_upload: {e}")
        await message.answer("❌ Tizimda xatolik yuz berdi. Iltimos keyinroq urinib ko'ring.")
        await state.clear()

@router.message(StateFilter(ActivityUploadState.waiting_for_photo), F.photo)
async def handle_activity_photo(message: types.Message, state):
    """
    Handles multiple photo uploads for Activities.
    Max 5 photos. State is NOT cleared until 5th photo or manual finish (implicit).
    """
    try:
        user_id = message.from_user.id
        
        # 1. Get Photo
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # 2. Find Pending Upload
        async for db in get_session():
             stmt = select(TgAccount).where(TgAccount.telegram_id == user_id)
             result = await db.execute(stmt)
             tg_account = result.scalars().first()
             
             if not tg_account:
                 await message.answer("❌ Sizning Telegram hisobingiz talaba profiliga ulanmagan.")
                 return

             # Find latest pending upload for this student
             # We look for the MOST RECENT one, regardless of whether it has files or not
             # because we are appending to it.
             stmt = select(PendingUpload).where(
                 PendingUpload.student_id == tg_account.student_id
             ).order_by(PendingUpload.created_at.desc())
             
             result = await db.execute(stmt)
             pending = result.scalars().first()
             
             if not pending:
                 await message.answer("⚠️ Faollik yuklash sessiyasi topilmadi. Ilovadan qayta urinib ko'ring.")
                 await state.clear()
                 return

             # 3. Append File ID
             current_ids = [fid for fid in (pending.file_ids or "").split(",") if fid]
             
             if len(current_ids) >= 5:
                 await message.answer("⚠️ Maksimal 5 ta rasm yuklashingiz mumkin. Ortiqcha rasm qabul qilinmadi.")
                 await state.clear()
                 return

             current_ids.append(file_id)
             pending.file_ids = ",".join(current_ids)
             
             await db.commit()
             
             # 4. Notify
             count = len(current_ids)
             if count >= 5:
                 await message.answer(f"✅ 5-rasm qabul qilindi. Limit tugadi.\n\nEndi ilovaga qaytib saqlash tugmasini bosing.")
                 await state.clear()
             else:
                 await message.answer(f"✅ {count}-rasm qabul qilindi.\n\nYana {5-count} ta yuklashingiz mumkin.")
                 
    except Exception as e:
        print(f"Error in handle_activity_photo: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

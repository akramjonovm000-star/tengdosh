from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, Student, StudentDocument
from keyboards.inline_kb import (
    get_student_documents_kb,
    get_student_documents_simple_kb,
    get_document_type_kb,
    get_student_main_menu_kb,
)
from models.states import DocumentAddStates

router = Router()


# ============================================================
# Helper — Student olish
# ============================================================

async def get_student(call_or_msg, session: AsyncSession):
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == call_or_msg.from_user.id)
    )
    if not tg or not tg.student_id:
        return None
    return await session.get(Student, tg.student_id)


# ============================================================
# 📂 Hujjatlar bo‘limi asosiy menyusi
# ============================================================

# ============================================================
# 📂 Hujjatlar bo‘limi (Direct List)
# ============================================================

@router.callback_query(F.data.in_({"student_documents", "student_documents:profile", "student_documents_list"}))
async def student_documents_list(call: CallbackQuery, session: AsyncSession):
    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"

    kb_rows = [
        [InlineKeyboardButton(text="📂 Mening hujjatlarim", callback_data="student_my_documents")],
        [InlineKeyboardButton(text="➕ Hujjat qo‘shish", callback_data="student_document_add")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_to)]
    ]

    text = (
        "📄 <b>Hujjatlar bo'limi</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )

    try:
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
    except:
        await call.message.delete()
        await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "student_my_documents")
async def student_my_documents(call: CallbackQuery, session: AsyncSession):
    student = await get_student(call, session)
    if not student: return

    # Fetch User Docs
    user_docs = (await session.scalars(
        select(StudentDocument).where(
            StudentDocument.student_id == student.id, 
            StudentDocument.file_type == "document"
        ).order_by(StudentDocument.uploaded_at.desc())
    )).all()

    kb_rows = []
    text = "📂 <b>Mening hujjatlarim:</b>\n\n"

    if not user_docs:
        text += "<i>Sizda shaxsiy hujjatlar yo'q.</i>"
    else:
        text += "Ma'lumotni ko'rish uchun hujjat nomini tanlang:"
        for doc in user_docs:
            # Button for each doc
            kb_rows.append([InlineKeyboardButton(text=f"📄 {doc.title}", callback_data=f"doc_open_{doc.id}")])

    # Back button to Documents Menu
    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_documents")])

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("doc_open_"))
async def open_user_document(call: CallbackQuery, session: AsyncSession):
    try:
        doc_id = int(call.data.split("_")[-1])
    except:
        return await call.answer("Xatolik", show_alert=True)

    doc = await session.get(StudentDocument, doc_id)
    if not doc:
        return await call.answer("Hujjat topilmadi", show_alert=True)

    await call.answer("📤 Hujjat yuklanmoqda...")
    
    caption = f"📄 <b>{doc.title}</b>\nKategoriya: {doc.category}"
    
    try:
        if doc.file_type == "photo":
            await call.message.answer_photo(doc.file_id, caption=caption, parse_mode="HTML")
        else:
            try:
                await call.message.answer_document(doc.file_id, caption=caption, parse_mode="HTML")
            except Exception as e:
                # Self-healing: If sent as document but it's actually a photo
                if "can't use file of type Photo as Document" in str(e):
                    doc.file_type = "photo"
                    await session.commit()
                    await call.message.answer_photo(doc.file_id, caption=caption, parse_mode="HTML")
                else:
                    raise e
            
        await call.message.answer(
            "Quyidagi tugma orqali menyuga qaytishingiz mumkin:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="go_student_home")]])
        )
        
    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")

# ============================================================
# 3) HUJJAT QO‘SHISH FLOW
# ============================================================

@router.callback_query(F.data == "student_document_add")
async def student_document_add(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await state.set_state(DocumentAddStates.TITLE)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_document")]])
    
    await call.message.edit_text(
        "📝 <b>Hujjat nomi:</b>\n\n"
        "Yangi hujjat uchun nom kiriting (masalan: <i>IELTS, Passport</i>):",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.message(DocumentAddStates.TITLE)
async def document_title_entered(message: Message, state: FSMContext):
    title = message.text
    if not title:
        return await message.answer("Iltimos, nom kiriting:")
        
    await state.update_data(title=title)
    await state.set_state(DocumentAddStates.FILE)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_document")]])

    await message.answer(
        f"✅ Nomi: <b>{title}</b>\n\n"
        "📎 <b>Endi hujjat faylini yuboring (Rasm yoki PDF):</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.message(DocumentAddStates.FILE)
async def process_file_upload(message: Message, state: FSMContext, session: AsyncSession):
    """
    Unified handler for file upload step.
    Captures ANY message in this state and checks content type manually.
    """
    file_id = None
    file_unique_id = None
    file_size = None
    mime_type = None
    file_type = "document"

    if message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        file_size = message.document.file_size
        mime_type = message.document.mime_type
        file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_unique_id = message.photo[-1].file_unique_id
        file_size = message.photo[-1].file_size
        mime_type = "image/jpeg"
        file_type = "photo"
    else:
        # Invalid content
        await message.answer("❌ Iltimos, <b>Fayl</b> yoki <b>Rasm</b> yuboring (PDF, JPG).", parse_mode="HTML")
        return

    # Valid content
    await state.update_data(
        file_id=file_id, 
        file_unique_id=file_unique_id,
        file_size=file_size,
        mime_type=mime_type,
        file_type=file_type
    )
    
    data = await state.get_data()
    title = data.get("title", "Hujjat")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="save_document")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_document")],
        ]
    )

    await message.answer(
        f"📄 <b>Tasdiqlash</b>\n\n"
        f"Nomi: {title}\n"
        f"Fayl: {file_type}\n\n"
        "Saqlashni tasdiqlaysizmi?",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "save_document")
async def save_document(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    student = await get_student(call, session)
    
    if not student:
        await call.answer("Auth Error")
        return

    title = data.get("title", "Hujjat")
    file_id = data.get("file_id")
    file_unique_id = data.get("file_unique_id")
    file_size = data.get("file_size")
    mime_type = data.get("mime_type")
    # Mapping 'photo' to 'document' category if it's a student doc
    file_type = "document"
    
    # Save to DB
    doc = StudentDocument(
        student_id=student.id,
        file_name=title,
        telegram_file_id=file_id,
        telegram_file_unique_id=file_unique_id,
        file_size=file_size,
        mime_type=mime_type,
        file_type=file_type,
        uploaded_by="student",
        is_active=True
    )
    session.add(doc)
    await session.commit()
    
    await state.clear()
    await call.message.edit_text(
        f"✅ <b>{title}</b> muvaffaqiyatli saqlandi!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="go_student_home")],
            [InlineKeyboardButton(text="📂 Mening hujjatlarim", callback_data="student_my_documents")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "cancel_document")
async def cancel_document(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.", reply_markup=get_student_documents_kb())
    await call.answer()

# ============================================================
# 8) MOBILE APP UPLOAD HANDLER
# ============================================================
from database.models import PendingUpload

@router.message(DocumentAddStates.WAIT_FOR_APP_FILE, F.photo | F.document)
async def on_mobile_document_upload(message: Message, state: FSMContext, session: AsyncSession):
    # logger.info(f"DEBUG: Document upload triggered for {message.from_user.id}")
    
    # Check TG Account
    stmt = select(TgAccount).where(TgAccount.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    tg = result.scalars().first()
    
    if not tg or not tg.student_id:
        await message.answer("Siz talaba emassiz yoki hisob ulanmagan.")
        return

    # Find active pending upload for this student
    # We prioritize the MOST RECENT pending upload
    stmt = (
        select(PendingUpload)
        .where(PendingUpload.student_id == tg.student_id)
        .order_by(PendingUpload.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    pending = result.scalars().first()

    if not pending:
        await state.clear()
        return await message.answer("Hozirda faol hujjat yuklash so'rovi mavjud emas.")

    # Save File ID and Metadata
    file_id = None
    file_unique_id = None
    file_size = 0
    mime_type = "application/octet-stream"

    if message.photo:
        # Best quality
        photo = message.photo[-1]
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        file_size = photo.file_size
        mime_type = "image/jpeg"
    elif message.document:
        doc = message.document
        file_id = doc.file_id
        file_unique_id = doc.file_unique_id
        file_size = doc.file_size
        mime_type = doc.mime_type
        
    # Notify User IMMEDIATELY
    await message.answer(
        "✅ <b>Hujjat qabul qilindi!</b>\n\n"
        "Iltimos, ilovaga qayting va <b>'Saqlash'</b> tugmasini bosing.",
        parse_mode="HTML"
    )

    # Update DB (Overwrite for single document upload flow)
    pending.file_ids = file_id
    pending.file_unique_id = file_unique_id
    pending.file_size = file_size
    pending.mime_type = mime_type
    
    # Mark as uploaded (optional, status serves this)
    pending.status = "uploaded"
    
    await session.commit()
    
    # Clear state so user isn't stuck
    await state.clear()





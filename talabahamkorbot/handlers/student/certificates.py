from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, Student, UserCertificate
from models.states import CertificateAddStates
from keyboards.inline_kb import get_student_certificates_kb, get_student_certificates_simple_kb

router = Router()

# ===== Helper: Studentni olish =====
async def get_student(call_or_msg, session: AsyncSession):
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == call_or_msg.from_user.id)
    )
    if not tg or not tg.student_id:
        return None
    return await session.get(Student, tg.student_id)

# ===== Asosiy menyu =====
@router.callback_query(F.data.startswith("student_certificates"))
async def student_certificates(call: CallbackQuery):
    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"

    text = (
        "🎓 <b>Sertifikatlar bo‘limi</b>\n"
        "Quyidagilardan birini tanlang:"
    )
    kb = get_student_certificates_kb(back_callback=back_to)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.delete()
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

# ===== 1) Sertifikatlar ro‘yxati (List) =====
@router.callback_query(F.data == "student_cert_list")
async def student_cert_list(call: CallbackQuery, session: AsyncSession):
    student = await get_student(call, session)
    if not student:
        await call.answer("Talaba topilmadi!", show_alert=True)
        return

    certs = await session.scalars(
        select(UserCertificate).where(UserCertificate.student_id == student.id).order_by(UserCertificate.id.desc())
    )
    certs = certs.all()

    if not certs:
        await call.message.edit_text(
            "📁 <b>Sizda hali sertifikatlar mavjud emas.</b>",
            reply_markup=get_student_certificates_simple_kb(), # Add button + Back
            parse_mode="HTML"
        )
        return

    # Generate list buttons
    kb_rows = []
    for cert in certs:
        kb_rows.append([
            InlineKeyboardButton(text=f"📜 {cert.title}", callback_data=f"open_cert:{cert.id}")
        ])
    
    # Navigation buttons
    kb_rows.append([InlineKeyboardButton(text="➕ Sertifikat qo‘shish", callback_data="student_cert_add")])
    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_certificates")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    await call.message.edit_text(
        "📂 <b>Sizning sertifikatlaringiz:</b>\n"
        "Ko'rish uchun ustiga bosing:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# ===== 2) Sertifikatni ochish (Open) =====
@router.callback_query(F.data.startswith("open_cert:"))
async def open_user_certificate(call: CallbackQuery, session: AsyncSession):
    try:
        cert_id = int(call.data.split(":")[1])
    except:
        return await call.answer("Xatolik", show_alert=True)

    cert = await session.get(UserCertificate, cert_id)
    if not cert:
        return await call.answer("Sertifikat topilmadi", show_alert=True)

    await call.answer("📤 Yuklanmoqda...")
    
    caption = f"📜 <b>{cert.title}</b>"
    
    try:
        # UserCertificate doesn't have file_type, so we try send_document (works for photos too usually)
        await call.message.answer_document(cert.file_id, caption=caption, parse_mode="HTML")
            
        await call.message.answer(
            "Quyidagi tugma orqali menyuga qaytishingiz mumkin:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="go_student_home")],
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_cert_list")]
            ])
        )
        
    except Exception as e:
        await call.message.answer(f"❌ Xatolik: {e}")

# ===== 3) Sertifikat qo‘shish (Add) =====
@router.callback_query(F.data == "student_cert_add")
async def student_cert_add(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(CertificateAddStates.TITLE)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_cert")]])
    
    await call.message.edit_text(
        "📝 <b>Sertifikat nomi:</b>\n\n"
        "Yangi sertifikat uchun nom kiriting (masalan: <i>IELTS, Coursera</i>):",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.message(CertificateAddStates.TITLE)
async def cert_title_entered(message: Message, state: FSMContext):
    title = message.text
    if not title:
        return await message.answer("Iltimos, nom kiriting:")
        
    await state.update_data(title=title)
    await state.set_state(CertificateAddStates.FILE)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_cert")]])

    await message.answer(
        f"✅ Nomi: <b>{title}</b>\n\n"
        "📎 <b>Endi sertifikat faylini yuboring (Faqat PDF):</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# Unified Upload Handler
@router.message(CertificateAddStates.FILE)
async def process_cert_upload(message: Message, state: FSMContext, session: AsyncSession):
    file_id = None
    
    # Check for document
    if message.document:
        # Validate PDF
        mime = message.document.mime_type or ""
        fname = message.document.file_name or ""
        
        if "pdf" in mime.lower() or fname.lower().endswith(".pdf"):
             file_id = message.document.file_id
        else:
             await message.answer("❌ Iltimos, faqat <b>PDF</b> formatdagi fayl yuboring.", parse_mode="HTML")
             return
             
    elif message.photo:
        await message.answer("❌ Rasm qabul qilinmaydi. Iltimos, <b>PDF</b> fayl yuboring.", parse_mode="HTML")
        return
    else:
        await message.answer("❌ Iltimos, <b>PDF</b> fayl yuboring.", parse_mode="HTML")
        return

    await state.update_data(file_id=file_id)
    
    data = await state.get_data()
    title = data.get("title", "Sertifikat")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="save_cert")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_cert")],
        ]
    )

    await message.answer(
        f"📄 <b>Tasdiqlash</b>\n\n"
        f"Nomi: {title}\n"
        "Saqlashni tasdiqlaysizmi?",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "save_cert")
async def save_certificate(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    student = await get_student(call, session)
    
    if not student:
        await call.answer("Auth Error")
        return

    title = data.get("title", "Sertifikat")
    file_id = data.get("file_id")
    
    cert = UserCertificate(
        student_id=student.id,
        title=title,
        file_id=file_id,
    )
    session.add(cert)
    await session.commit()
    
    await state.clear()
    await call.message.edit_text(
        f"✅ <b>{title}</b> muvaffaqiyatli saqlandi!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📁 Sertifikatlarim", callback_data="student_cert_list")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="go_student_home")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "cancel_cert")
async def cancel_certificate(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.", reply_markup=get_student_certificates_kb())
    await call.answer()

# ============================================================
# 8) MOBILE APP UPLOAD HANDLER
# ============================================================
from database.models import PendingUpload

@router.message(CertificateAddStates.WAIT_FOR_APP_FILE, F.photo | F.document)
async def on_mobile_certificate_upload(message: Message, state: FSMContext, session: AsyncSession):
    student = await get_student(message, session)
    if not student:
        return await message.answer("Siz talaba emassiz.")

    # Find active pending upload for this student
    pending = await session.scalar(
        select(PendingUpload)
        .where(PendingUpload.student_id == student.id)
        .order_by(PendingUpload.created_at.desc())
        .limit(1)
    )

    if not pending:
        await state.clear()
        return await message.answer("Hozirda faol sertifikat yuklash so'rovi mavjud emas.")

    # Save File ID
    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id
        
    # Notify User
    await message.answer(
        "✅ <b>Sertifikat qabul qilindi!</b>\n\n"
        "Iltimos, ilovaga qayting va <b>'Saqlash'</b> tugmasini bosing.",
        parse_mode="HTML"
    )

    # Update DB (Overwrite for single certificate upload flow)
    pending.file_ids = file_id
    await session.commit()
    
    await state.clear()

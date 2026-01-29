"""
6 yo'nalish bo'yicha ish - Kengaytirilgan (Talabasiz)
"""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Staff, TgAccount, TyutorWorkLog
from models.states import TyutorWorkStates

router = Router()

DIRECTIONS = {
    "normativ": "📜 I. Normativ hujjatlar",
    "darsdan_tashqari": "🎯 II. Darsdan tashqari vaqt",
    "manaviy": "🌟 III. Ma'naviy-ma'rifiy",
    "profilaktika": "⚠️ IV. Profilaktika",
    "turar_joy": "🏠 V. Turar joy nazorati",
    "ota_ona": "👨‍👩‍👧 VI. Ota-ona aloqasi"
}


async def _get_tyutor_by_tg(telegram_id: int, session: AsyncSession):
    tg_acc = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == telegram_id)
    )
    if not tg_acc or not tg_acc.staff_id:
        return None
    staff = await session.get(Staff, tg_acc.staff_id)
    if staff and staff.role == "tyutor":
        return staff
    return None


@router.callback_query(F.data == "tyutor_work_directions")
async def tyutor_work_directions_menu(call: CallbackQuery, session: AsyncSession):
    """6 yo'nalish asosiy menyu"""
    tyutor = await _get_tyutor_by_tg(call.from_user.id, session)
    
    if not tyutor:
        await call.answer("❌ Xatolik", show_alert=True)
        return
    
    text = """
✅ <b>6 YO'NALISH BO'YICHA ISH</b>

Quyidagi yo'nalishlardan birini tanlang va bajargan ishingizni kiriting:
"""
    
    keyboard = []
    for key, label in DIRECTIONS.items():
        keyboard.append([
            InlineKeyboardButton(text=label, callback_data=f"tyutor_direction:{key}")
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="tyutor_dashboard")
    ])
    
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("tyutor_direction:"))
async def tyutor_select_direction(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Yo'nalish tanlash -> Nomini kiriting (Talaba tanlash tashlab ketildi)"""
    tyutor = await _get_tyutor_by_tg(call.from_user.id, session)
    
    if not tyutor:
        await call.answer("❌ Xatolik", show_alert=True)
        return
    
    direction = call.data.split(":")[1]
    
    await state.set_state(TyutorWorkStates.entering_title)
    await state.update_data(
        tyutor_id=tyutor.id,
        direction=direction,
        student_id=None # EXPLICITLY NONE
    )
    
    await call.message.edit_text(
        f"📝 <b>{DIRECTIONS[direction]}</b>\n\n"
        "1. Iltimos, bajarilgan ish <b>nomini</b> (qisqacha) kiriting:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="tyutor_work_directions")]
        ])
    )


@router.message(TyutorWorkStates.entering_title)
async def process_title(message: Message, state: FSMContext):
    """Nom qabul qilindi -> Tavsif so'rash"""
    title = message.text
    if not title:
        await message.answer("⚠️ Iltimos, matn kiriting.")
        return

    await state.update_data(work_title=title)
    await state.set_state(TyutorWorkStates.entering_description)
    
    await message.answer(
        "2. Endi batafsil <b>tavsif</b> (izoh) yozing:\n"
        "<i>(Agar kerak bo'lmasa /skip deb yozing)</i>",
        parse_mode="HTML"
    )


@router.message(TyutorWorkStates.entering_description)
async def process_description(message: Message, state: FSMContext):
    """Tavsif qabul qilindi -> Sana so'rash"""
    desc = message.text
    if not desc:
         await message.answer("⚠️ Matn kiriting.")
         return
         
    actual_desc = desc if desc != "/skip" else None
    await state.update_data(work_desc=actual_desc)
    
    await state.set_state(TyutorWorkStates.entering_date)
    await message.answer(
        "3. Bajarilgan <b>sanani</b> kiriting (KK.OO.YYYY formatda):\n"
        "Masalan: <i>16.12.2025</i>",
        parse_mode="HTML"
    )


@router.message(TyutorWorkStates.entering_date)
async def process_date(message: Message, state: FSMContext):
    """Sana qabul qilindi -> Rasm so'rash"""
    date_text = message.text
    
    await state.update_data(work_date=date_text)
    await state.set_state(TyutorWorkStates.uploading_photo)
    
    await message.answer(
        "4. Oxirgi bosqich: <b>Rasm</b> yoki <b>Fayl</b> yuklang (isboti uchun):\n"
        "<i>(Agar rasm yo'q bo'lsa /skip deb yozing)</i>",
        parse_mode="HTML"
    )


@router.message(TyutorWorkStates.uploading_photo)
async def process_photo_and_save(message: Message, session: AsyncSession, state: FSMContext):
    """Rasm qabul qilindi -> Saqlash (Pending)"""
    data = await state.get_data()
    
    file_id = None
    file_type = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.text == "/skip":
        pass
    else:
        await message.answer("⚠️ Rasm, fayl yuklang yoki /skip deb yozing.")
        return

    # DB ga saqlash
    new_log = TyutorWorkLog(
        tyutor_id=data["tyutor_id"],
        student_id=None, # <--- TALABASIZ
        direction_type=data["direction"],
        title=data.get("work_title"),
        description=data.get("work_desc"),
        completion_date=data.get("work_date"),
        file_id=file_id,
        file_type=file_type,
        status="pending",
        points=0
    )
    
    session.add(new_log)
    await session.commit()
    
    await state.clear()
    
    # Confirmation Msg
    await message.answer(
        f"✅ <b>Ish muvaffaqiyatli yuborildi!</b>\n\n"
        f"Yo'nalish: {DIRECTIONS[data['direction']]}\n"
        f"Holati: ⏳ <b>Tekshirilmoqda</b>\n\n"
        "Dekanat yoki Rahbariyat tasdiqlaganidan so'ng ball beriladi.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
             [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="tyutor_dashboard")]
        ])
    )

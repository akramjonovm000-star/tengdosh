from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from keyboards.inline_kb import (
    get_tutor_main_menu_kb,
    get_tutor_activity_menu_kb,
    get_tutor_student_lookup_back_kb
)
from database.models import Staff, Student, TutorGroup, TgAccount
from models.states import TutorBroadcastStates
from keyboards.inline_kb import (
    get_tutor_main_menu_kb,
    get_tutor_activity_menu_kb,
    get_tutor_student_lookup_back_kb,
    get_tutor_broadcast_back_kb,
    get_tutor_broadcast_confirm_kb
)

router = Router()


# ============================================================
# 1) TYUTOR ASOSIY MENYUSI
# ============================================================
@router.callback_query(F.data == "tutor_menu")
async def tutor_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🧑‍🏫 <b>Tyutor bo‘limi</b>\nQuyidagilardan birini tanlang:",
        reply_markup=get_tutor_main_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()


# ============================================================
# 2) Guruhga e’lon
# ============================================================
@router.callback_query(F.data == "tutor_broadcast")
async def tutor_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(TutorBroadcastStates.WAITING_CONTENT)
    await call.message.edit_text(
        "📣 <b>Guruh talabalariga e’lon yuborish.</b>\n\n"
        "Matn, rasm, video yoki fayl yuborishingiz mumkin:",
        reply_markup=get_tutor_broadcast_back_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(TutorBroadcastStates.WAITING_CONTENT)
async def tutor_broadcast_content(message: Message, state: FSMContext):
    data = {}
    if message.photo:
        data["file_type"] = "photo"
        data["file_id"] = message.photo[-1].file_id
        data["text"] = message.caption or ""
    elif message.video:
        data["file_type"] = "video"
        data["file_id"] = message.video.file_id
        data["text"] = message.caption or ""
    elif message.voice:
        data["file_type"] = "voice"
        data["file_id"] = message.voice.file_id
        data["text"] = message.caption or ""
    elif message.document:
        data["file_type"] = "document"
        data["file_id"] = message.document.file_id
        data["text"] = message.caption or ""
    elif message.text:
        data["file_type"] = "text"
        data["file_id"] = None
        data["text"] = message.text
    else:
        await message.answer("⚠️ Iltimos, matn yoki media fayl yuboring.")
        return

    await state.update_data(**data)
    await state.set_state(TutorBroadcastStates.CONFIRM)

    preview_text = f"📢 <b>Xabar ko‘rinishi:</b>\n\n{data['text']}\n\n<i>Yuborishni tasdiqlaysizmi?</i>"

    if data["file_id"]:
        if data["file_type"] == "photo":
            await message.answer_photo(
                data["file_id"], caption=preview_text,
                reply_markup=get_tutor_broadcast_confirm_kb(), parse_mode="HTML"
            )
        elif data["file_type"] == "video":
            await message.answer_video(
                data["file_id"], caption=preview_text,
                reply_markup=get_tutor_broadcast_confirm_kb(), parse_mode="HTML"
            )
        elif data["file_type"] == "voice":
            await message.answer_voice(
                data["file_id"], caption=preview_text,
                reply_markup=get_tutor_broadcast_confirm_kb(), parse_mode="HTML"
            )
        elif data["file_type"] == "document":
            await message.answer_document(
                data["file_id"], caption=preview_text,
                reply_markup=get_tutor_broadcast_confirm_kb(), parse_mode="HTML"
            )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_tutor_broadcast_confirm_kb(),
            parse_mode="HTML"
        )


@router.callback_query(
    TutorBroadcastStates.CONFIRM,
    F.data == "tutor_broadcast_confirm"
)
async def tutor_broadcast_confirm(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    
    # Tyutor ma'lumotlarini olish
    staff = await session.scalar(
        select(Staff).join(TgAccount).where(TgAccount.telegram_id == call.from_user.id)
    )
    
    if not staff:
        await call.answer("❌ Xatlik: Xodim topilmadi", show_alert=True)
        return

    # Tyutorning guruhlarini topish
    tutor_groups = await session.scalars(
        select(TutorGroup.group_number).where(TutorGroup.tutor_id == staff.id)
    )
    group_numbers = tutor_groups.all()
    
    if not group_numbers:
        await call.answer("⚠️ Sizga biriktirilgan guruhlar yo'q", show_alert=True)
        return

    # Faqat shu guruhlar talabalariga
    students = await session.scalars(
        select(TgAccount.telegram_id)
        .join(Student)
        .where(Student.group_number.in_(group_numbers)) # group_number string matching
    )
    
    bot = call.bot
    sent = 0
    
    for tg_id in students.all():
        try:
            if data["file_id"]:
                if data["file_type"] == "photo":
                    await bot.send_photo(tg_id, data["file_id"], caption=data["text"])
                elif data["file_type"] == "video":
                    await bot.send_video(tg_id, data["file_id"], caption=data["text"])
                elif data["file_type"] == "voice":
                    await bot.send_voice(tg_id, data["file_id"])
                elif data["file_type"] == "document":
                    await bot.send_document(tg_id, data["file_id"], caption=data["text"])
            else:
                await bot.send_message(tg_id, data["text"])
            sent += 1
        except Exception:
            continue
            
    await state.clear()
    
    await call.message.delete() # Preview xabarni o'chirish
    await call.message.answer(
        f"✅ <b>Xabar yuborildi</b>\n\n"
        f"👥 Guruh talabalari: <b>{sent} ta</b>",
        reply_markup=get_tutor_main_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(
    TutorBroadcastStates.CONFIRM,
    F.data == "tutor_broadcast_cancel"
)
async def tutor_broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.set_state(TutorBroadcastStates.WAITING_CONTENT)
    await call.message.delete()
    await call.message.answer(
        "❌ Xabar bekor qilindi.\n\n"
        "✍️ Yangi xabar yuboring yoki menyuga qayting:",
        reply_markup=get_tutor_broadcast_back_kb()
    )
    await call.answer()


# ============================================================
# 3) Feedback (murojaatlar)
# ❗ Bu bo‘lim staff/feedback.py orqali boshqariladi.
# ❗ Shu sababli bu faylda hech qanday handler yozilmaydi.
# ============================================================

# ❌ Eski “tez orada ishlaydi” handler O‘CHIRILDI.
# @router.callback_query(F.data == "tutor_feedback") ...


# ============================================================
# 4) TALABA QIDIRISH (REDUNDANT - REMOVED)
# ❗ staff/student_lookup.py orqali ishlaydi (tt_student_lookup)
# ============================================================


# ============================================================
# 6) FAOLLIK TASDIQLASH MENYUSI
# ============================================================


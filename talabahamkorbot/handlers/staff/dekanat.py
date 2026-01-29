from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import StudentFeedback

from keyboards.inline_kb import (
    get_dekanat_main_menu_kb,
    get_dek_activity_menu_kb,
    get_dek_student_lookup_back_kb
)
from database.models import Student, Staff, TgAccount
from models.states import DekBroadcastStates, DekanatAppealStates
from keyboards.inline_kb import (
    get_dekanat_main_menu_kb,
    get_dek_activity_menu_kb,
    get_dek_student_lookup_back_kb,
    get_dek_broadcast_back_kb,
    get_dek_broadcast_confirm_kb,
    get_dekanat_appeal_actions_kb
)

router = Router()


# ============================================================
# 1) DEKANAT ASOSIY MENYUSI
# ============================================================
@router.callback_query(F.data == "dek_menu")
async def dekanat_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🏫 <b>Dekanat bo‘limi</b>\nQuyidagi bo‘limlardan birini tanlang:",
        reply_markup=get_dekanat_main_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()


# ============================================================
# 2) Fakultet bo‘yicha e’lon
# ============================================================
@router.callback_query(F.data == "dek_broadcast")
async def dek_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(DekBroadcastStates.WAITING_CONTENT)
    await call.message.edit_text(
        "📣 <b>Fakultet talabalariga e’lon yuborish.</b>\n\n"
        "Matn, rasm, video yoki fayl yuborishingiz mumkin:",
        reply_markup=get_dek_broadcast_back_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(DekBroadcastStates.WAITING_CONTENT)
async def dek_broadcast_content(message: Message, state: FSMContext):
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
    await state.set_state(DekBroadcastStates.CONFIRM)

    preview_text = f"📢 <b>Xabar ko‘rinishi:</b>\n\n{data['text']}\n\n<i>Yuborishni tasdiqlaysizmi?</i>"

    if data["file_id"]:
        if data["file_type"] == "photo":
            await message.answer_photo(
                data["file_id"], caption=preview_text,
                reply_markup=get_dek_broadcast_confirm_kb(), parse_mode="HTML"
            )
        elif data["file_type"] == "video":
            await message.answer_video(
                data["file_id"], caption=preview_text,
                reply_markup=get_dek_broadcast_confirm_kb(), parse_mode="HTML"
            )
        elif data["file_type"] == "voice":
            await message.answer_voice(
                data["file_id"], caption=preview_text,
                reply_markup=get_dek_broadcast_confirm_kb(), parse_mode="HTML"
            )
        elif data["file_type"] == "document":
            await message.answer_document(
                data["file_id"], caption=preview_text,
                reply_markup=get_dek_broadcast_confirm_kb(), parse_mode="HTML"
            )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_dek_broadcast_confirm_kb(),
            parse_mode="HTML"
        )


@router.callback_query(
    DekBroadcastStates.CONFIRM,
    F.data == "dek_broadcast_confirm"
)
async def dek_broadcast_confirm(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    
    # Dekanat ma'lumotlarini olish (fakultet ID kerak)
    staff = await session.scalar(
        select(Staff).join(TgAccount).where(TgAccount.telegram_id == call.from_user.id)
    )
    
    if not staff or not staff.faculty_id:
        await call.answer("❌ Xatlik: Fakultet biriktirilmagan", show_alert=True)
        return

    # Faqat shu fakultet talabalariga
    students = await session.scalars(
        select(TgAccount.telegram_id)
        .join(Student)
        .where(Student.faculty_id == staff.faculty_id)
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
        f"👥 Fakultet talabalari: <b>{sent} ta</b>",
        reply_markup=get_dekanat_main_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(
    DekBroadcastStates.CONFIRM,
    F.data == "dek_broadcast_cancel"
)
async def dek_broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.set_state(DekBroadcastStates.WAITING_CONTENT)
    await call.message.delete()
    await call.message.answer(
        "❌ Xabar bekor qilindi.\n\n"
        "✍️ Yangi xabar yuboring yoki menyuga qayting:",
        reply_markup=get_dek_broadcast_back_kb()
    )
    await call.answer()


# ============================================================
# 3) Murojaatlar (feedback) bo‘limi
#  ❗ Bu joy staff/feedback.py modulida ishlaydi!
#  ❗ Shuning uchun bu faylda hech narsa yozilmaydi.
# ============================================================

# ❌ eski noto'g'ri handler O‘CHIRILDI:
# @router.callback_query(F.data == "dek_feedback") ...


# ============================================================
# 4) TALABA QIDIRISH — BOSHLASH
# ============================================================
@router.callback_query(F.data == "dek_student_lookup")
async def dek_lookup_start(call: CallbackQuery, state: FSMContext):
    await state.set_state("dek_lookup_hemis")
    await call.message.edit_text(
        "🔍 Talabaning HEMIS loginini kiriting:",
        reply_markup=get_dek_student_lookup_back_kb()
    )
    await call.answer()


# ============================================================
# 5) TALABA QIDIRISH — LOGIN QABUL QILISH
# ============================================================
@router.message(F.state == "dek_lookup_hemis")
async def dek_lookup_process(message: Message, session: AsyncSession, state: FSMContext):

    hemis = message.text.strip()

    # Dekanat xodimini TG orqali topamiz
    staff = await session.scalar(
        select(Staff).where(Staff.telegram_id == message.from_user.id)
    )

    if not staff:
        await message.answer("❌ Xodim aniqlanmadi.")
        return

    # Talabani qidirish
    student = await session.scalar(
        select(Student).where(Student.hemis_login == hemis)
    )

    if not student:
        await message.answer("❌ Bunday talaba topilmadi.")
        return

    # Fakultet filtri
    if student.faculty_id != staff.faculty_id:
        await message.answer("⛔ Bu talaba sizning fakultetingizga tegishli emas.")
        return

    # Talaba ma’lumotlarini chiqaramiz
    await message.answer(
        f"🎓 <b>{student.full_name}</b>\n"
        f"📘 Fakultet: {student.faculty_id}\n"
        f"👥 Guruh: {student.group_number}\n\n"
        "⬇️ Talaba bo‘limlari yuklanmoqda...",
        parse_mode="HTML"
    )

    await state.clear()


# ============================================================
# 6) FAOLLIK TASDIQLASH MENYUSI
# ============================================================


@router.callback_query(F.data == "dekan_view_appeals")
async def dekan_view_appeals(
    call: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    staff = await session.scalar(
        select(Staff)
        .join(TgAccount)
        .where(TgAccount.telegram_id == call.from_user.id)
    )

    appeals = await session.scalars(
        select(StudentFeedback)
        .where(
            StudentFeedback.assigned_role == "dekanat",
            StudentFeedback.assigned_staff_id == staff.id,
            StudentFeedback.status == "assigned_dekanat"
        )
        .order_by(StudentFeedback.created_at)
    )

    appeals = appeals.all()

    if not appeals:
        await call.message.edit_text("📭 Sizga biriktirilgan murojaatlar yo‘q.")
        await call.answer()
        return

    await state.set_state(DekanatAppealStates.viewing)
    await state.update_data(
        appeal_ids=[a.id for a in appeals],
        index=0
    )

    await send_dekan_appeal(call.message, appeals[0], session)
    await call.answer()

async def send_dekan_appeal(msg, appeal: StudentFeedback, session: AsyncSession):
    student = await session.get(Student, appeal.student_id)

    text = (
        "📨 <b>Talaba murojaati</b>\n\n"
        f"👤 <b>{student.full_name}</b>\n"
        f"🆔 HEMIS: <code>{student.hemis_login}</code>\n\n"
        f"{appeal.text or ''}"
    )

    kb = get_dekanat_appeal_actions_kb(appeal.id)

    if appeal.file_type == "document":
        await msg.answer_document(appeal.file_id, caption=text, reply_markup=kb, parse_mode="HTML")
    elif appeal.file_type == "photo":
        await msg.answer_photo(appeal.file_id, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")

#@router.callback_query(F.data.startswith("dekan_close:"))
async def dekan_close(
    call: CallbackQuery,
    session: AsyncSession
):
    appeal_id = int(call.data.split(":")[1])
    appeal = await session.get(StudentFeedback, appeal_id)

    appeal.status = "closed"
    await session.commit()

    await call.message.edit_text("✅ Murojaat yopildi.")
    await call.answer()

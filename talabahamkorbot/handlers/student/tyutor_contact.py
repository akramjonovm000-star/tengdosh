"""
Student - Tyutor Contact Handler
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Student, TutorGroup, Staff, TgAccount, StudentFeedback
from models.states import FeedbackStates
from keyboards.inline_kb import get_student_main_menu_kb, get_feedback_anonymity_kb

router = Router()


async def _get_student(user_id: int, session: AsyncSession) -> Student | None:
    tg_acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id))
    if not tg_acc or not tg_acc.student_id:
        return None
    return await session.get(Student, tg_acc.student_id)


@router.callback_query(F.data == "student_tyutor_contact")
async def view_tyutor_info(call: CallbackQuery, session: AsyncSession):
    """Mening Tyutorim ma'lumotlari"""
    student = await _get_student(call.from_user.id, session)
    if not student:
        await call.answer("❌ Talaba profili topilmadi", show_alert=True)
        return

    # Tyutorni topish
    result = await session.execute(
        select(Staff)
        .join(TutorGroup, TutorGroup.tutor_id == Staff.id)
        .where(TutorGroup.group_number == student.group_number)
    )
    tyutor = result.scalar_one_or_none()

    if not tyutor:
        text = (
            "⚠️ <b>Sizga tyutor biriktirilmagan.</b>\n\n"
            "Iltimos, dekanatga murojaat qiling yoki guruhingiz raqamini tekshiring."
        )
        await call.message.edit_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_student_home")]
            ])
        )
        return

    text = f"""
👤 <b>MENING TYUTORIM</b>

<b>Ism-familiya:</b> {tyutor.full_name}
<b>Telefon:</b> {tyutor.id} (balki telefon ustuni yo'qdir, hozircha ID)
<b>Guruh:</b> {student.group_number}

Agar savollaringiz bo'lsa, to'g'ridan-to'g'ri murojaat yuborishingiz mumkin.
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data=f"student_send_tyutor:{tyutor.id}")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_home")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("student_send_tyutor:"))
async def start_tyutor_message(call: CallbackQuery, state: FSMContext):
    """Tyutorga xabar yuborishni boshlash"""
    tyutor_id = int(call.data.split(":")[1])
    
    await state.set_state(FeedbackStates.waiting_message)
    await state.update_data(
        recipient_role="tyutor",
        assigned_staff_id=tyutor_id,
        is_anonymous=False  # Tyutorga ochiq yozish maqsadga muvofiq
    )
    
    text = """
✉️ <b>Tyutorga xabar yuborish</b>

Xabaringizni yozib qoldiring. Rasm yoki fayl ilova qilishingiz mumkin.
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="student_tyutor_contact")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

# Izoh: Xabar yuborish logikasi `handlers/student/feedback.py` dagi message handler orqali ishlaydi,
# chunki biz `FeedbackStates.waiting_message` holatiga o'tdik va kerakli ma'lumotlarni (recipient_role, assigned_staff_id) saqladik.
# `feedback.py` dagi handler buni tekshirib, to'g'ri maydonlarni to'ldirishi kerak.

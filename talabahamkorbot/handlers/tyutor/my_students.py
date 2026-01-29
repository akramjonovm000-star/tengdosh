"""
Mening talabalarim - Tyutor talabalar ro'yxati
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import (
    Staff, TgAccount, Student, TutorGroup,
    UserActivity, StudentFeedback, StudentRiskAssessment
)

router = Router()


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


from aiogram.exceptions import TelegramBadRequest

@router.callback_query(F.data == "tyutor_my_students")
async def tyutor_my_students(call: CallbackQuery, session: AsyncSession):
    """Tyutor talabalar ro'yxati"""
    print(f"DEBUG: tyutor_my_students called by {call.from_user.id}")
    tyutor = await _get_tyutor_by_tg(call.from_user.id, session)
    
    if not tyutor:
        await call.answer("❌ Xatolik", show_alert=True)
        return
    
    # Talabalarni olish
    result = await session.execute(
        select(Student)
        .join(TutorGroup, Student.group_number == TutorGroup.group_number)
        .where(TutorGroup.tutor_id == tyutor.id)
        .order_by(Student.group_number, Student.full_name)
    )
    students = result.scalars().all()
    
    if not students:
        text = "❌ Sizga biriktirilgan talabalar yo'q"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="tyutor_dashboard")]
        ])
        await call.message.edit_text(text, reply_markup=keyboard)
        return
    
    text = f"""
👥 <b>MENING TALABALARIM</b>

<b>Jami:</b> {len(students)} ta talaba
"""
    
    keyboard = []
    for student in students[:30]:  # Birinchi 30 ta
        # Risk darajasini olish
        result = await session.execute(
            select(StudentRiskAssessment).where(
                StudentRiskAssessment.student_id == student.id
            )
        )
        risk = result.scalar_one_or_none()
        
        # Risk emoji
        risk_emoji = ""
        if risk:
            if risk.risk_level == "critical":
                risk_emoji = "🔴"
            elif risk.risk_level == "high":
                risk_emoji = "🟠"
            elif risk.risk_level == "medium":
                risk_emoji = "🟡"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{risk_emoji} {student.full_name} ({student.group_number})",
                callback_data=f"tyutor_student_detail:{student.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="tyutor_dashboard")
    ])
    
    try:
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except TelegramBadRequest:
        await call.answer("✅ Ro'yxat yangilandi", show_alert=False)


@router.callback_query(F.data.startswith("tyutor_student_detail:"))
async def tyutor_student_detail(call: CallbackQuery, session: AsyncSession):
    """Talaba tafsilotlari"""
    student_id = int(call.data.split(":")[1])
    
    student = await session.get(Student, student_id)
    
    if not student:
        await call.answer("❌ Talaba topilmadi", show_alert=True)
        return
    
    # Faolliklar soni
    result = await session.execute(
        select(func.count(UserActivity.id))
        .where(UserActivity.student_id == student_id)
    )
    activities_count = result.scalar() or 0
    
    # Murojaatlar soni
    result = await session.execute(
        select(func.count(StudentFeedback.id))
        .where(StudentFeedback.student_id == student_id)
    )
    feedbacks_count = result.scalar() or 0
    
    # Risk darajasi
    result = await session.execute(
        select(StudentRiskAssessment).where(
            StudentRiskAssessment.student_id == student_id
        )
    )
    risk = result.scalar_one_or_none()
    
    risk_text = "🟢 Past" if not risk else {
        "low": "🟢 Past",
        "medium": "🟡 O'rtacha",
        "high": "🟠 Yuqori",
        "critical": "🔴 Juda yuqori"
    }.get(risk.risk_level, "🟢 Past")
    
    text = f"""
👤 <b>TALABA TAFSILOTLARI</b>

<b>Ism:</b> {student.full_name}
<b>Guruh:</b> {student.group_number}
<b>Telefon:</b> {student.phone or 'Kiritilmagan'}

━━━━━━━━━━━━━━━━━━━━━━

📊 <b>STATISTIKA:</b>

🎯 Faolliklar: {activities_count} ta
📝 Murojaatlar: {feedbacks_count} ta
⚠️ Xavf darajasi: {risk_text}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📂 Faolliklari", callback_data=f"staff_student_activities:{student_id}"),
        ],
        [
            InlineKeyboardButton(text="📝 Murojaatlari", callback_data=f"staff_student_appeals:{student_id}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="tyutor_my_students")
        ]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

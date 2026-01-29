from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Student

router = Router()

@router.callback_query(F.data == "view_students")
async def view_students(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    current_role = data.get("current_role")

    # Agar tyutor bo'lsa — faqat o'z guruhlari bo‘yicha talabalari chiqadi
    if current_role == "tyutor":
        tutor_id = data.get("tutor_id")
        from database.repo.utils import get_tutor_students

        students = await get_tutor_students(session, tutor_id)

        if not students:
            await call.message.answer("❌ Sizga biriktirilgan talabalar topilmadi.")
            return

        text = "📘 <b>Sizning guruhlaringizdagi talabalar:</b>\n\n"
        for s in students:
            text += f"👤 {s.full_name} — <code>{s.group_number}</code>\n"

        await call.message.answer(text)
        return

    # Aks holda — adminlar uchun umumiy ro‘yxat
    all_students = await session.execute(select(Student).order_by(Student.full_name))
    all_students = all_students.scalars().all()

    text = "📘 <b>Barcha talabalar:</b>\n\n"
    for s in all_students:
        text += f"👤 {s.full_name} — <code>{s.group_number}</code>\n"

    await call.message.answer(text)

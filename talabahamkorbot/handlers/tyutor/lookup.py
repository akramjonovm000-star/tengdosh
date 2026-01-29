"""
Tyutor uchun Talaba Qidirish (Alohida modul)
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database.models import Staff, Student, UserActivity, StudentFeedback, TgAccount, StaffRole, TutorGroup, Faculty
from aiogram.fsm.state import StatesGroup, State

router = Router()

class TyutorLookupStates(StatesGroup):
    waiting_query = State()


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


@router.callback_query(F.data == "tt_student_lookup")
async def tyutor_lookup_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(TyutorLookupStates.waiting_query)
    
    await call.message.edit_text(
        "🔍 <b>Talaba qidirish (Mening guruhlarimdan)</b>\n\n"
        "Talabaning <b>ism-familiyasini</b> yoki <b>HEMIS ID</b> raqamini yozing:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="tyutor_dashboard")
        ]])
    )


@router.message(TyutorLookupStates.waiting_query)
async def tyutor_lookup_process(message: Message, session: AsyncSession, state: FSMContext):
    query = message.text.strip()
    
    tyutor = await _get_tyutor_by_tg(message.from_user.id, session)
    if not tyutor:
        await message.answer("❌ Tyutor aniqlanmadi")
        return
    
    # Guruhlarimni olish
    groups = await session.scalars(select(TutorGroup).where(TutorGroup.tutor_id == tyutor.id))
    my_groups = [g.group_number for g in groups]
    
    if not my_groups:
        await message.answer("⚠️ Sizga guruhlar biriktirilmagan.")
        return
        
    # Search logic
    import difflib
    
    # Fetch ALL students in my groups (Optimization: fetching minimal columns if possible, but ORM fetches objects)
    # Since dataset is small (max ~200), this is acceptable.
    stmt = select(Student).where(Student.group_number.in_(my_groups))
    all_students = (await session.scalars(stmt)).all()
    
    matches = []
    
    if query.isdigit():
        # HEMIS ID search (Exact or contains)
        matches = [s for s in all_students if query in s.hemis_login]
    else:
        # Name search (Fuzzy)
        # 1. Exact/Substring match (High priority)
        exact_matches = [s for s in all_students if query.lower() in s.full_name.lower()]
        
        # 2. Fuzzy match
        # Create a map of name -> student
        name_map = {s.full_name: s for s in all_students}
        names = list(name_map.keys())
        
        # Get close matches (cutoff=0.4 allows for ~40% similarity, i.e. typos)
        # 'n=15' limits results
        similar_names = difflib.get_close_matches(query, names, n=15, cutoff=0.4)
        
        fuzzy_matches = [name_map[name] for name in similar_names]
        
        # Combine unique: Exact first, then Fuzzy
        seen_ids = set()
        for s in exact_matches:
            matches.append(s)
            seen_ids.add(s.id)
            
        for s in fuzzy_matches:
            if s.id not in seen_ids:
                matches.append(s)
                seen_ids.add(s.id)
    
    students = matches
    
    if not students:
        await message.answer(
            f"❌ <b>'{query}'</b> bo'yicha sizning guruhlaringizda talaba topilmadi.\n"
            "Qayta urinib ko'ring:",
            parse_mode="HTML"
        )
        return
        
    if len(students) > 1:
        text = "🔍 <b>Natijalar:</b>\n\n"
        for i, s in enumerate(students[:15], 1):
             text += f"{i}. <b>{s.full_name}</b> ({s.group_number}) - <code>{s.hemis_login}</code>\n"
        
        text += "\n⚠️ Aniqroq qidirish uchun to'liqroq yozing."
        await message.answer(text, parse_mode="HTML")
        return

    # Single Result
    await show_student_profile_tyutor(message, students[0], session)
    await state.clear()


async def show_student_profile_tyutor(message: Message, student: Student, session: AsyncSession):
    # Counts
    act_stats = await session.execute(
        select(UserActivity.status, func.count(UserActivity.id))
        .where(UserActivity.student_id == student.id)
        .group_by(UserActivity.status)
    )
    counts = dict(act_stats.all())
    
    appeal_count = await session.scalar(
        select(func.count(StudentFeedback.id)).where(StudentFeedback.student_id == student.id)
    )
    
    faculty_name = ""
    if student.faculty_id:
        fac = await session.get(Faculty, student.faculty_id)
        if fac: faculty_name = fac.name

    text = (
        f"🎓 <b>TALABA PROFILI</b>\n\n"
        f"👤 <b>{student.full_name}</b>\n"
        f"🆔 HEMIS: <code>{student.hemis_login}</code>\n"
        f"🏫 Fakultet: {faculty_name}\n"
        f"👥 Guruh: {student.group_number}\n"
        f"📞 Tel: {student.phone or '---'}\n\n"
        f"📊 <b>Faolliklar:</b>\n"
        f"✅ Tasdiqlangan: {counts.get('confirmed', 0)}\n"
        f"⏳ Kutishda: {counts.get('pending', 0)}\n\n"
        f"📨 Murojaatlar: {appeal_count}"
    )
    
    # Tyutor actions? Maybe just Back
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Dashboardga qaytish", callback_data="tyutor_dashboard")]
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

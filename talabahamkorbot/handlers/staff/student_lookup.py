from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from database.models import Staff, Student, UserActivity, StudentFeedback, TgAccount, StaffRole, Faculty
from models.states import StaffStudentLookupStates
from keyboards.inline_kb import (
    get_staff_student_lookup_back_kb, 
    get_student_profile_actions_kb,
    get_rahbariyat_main_menu_kb,
    get_dekanat_main_menu_kb,
    get_tutor_main_menu_kb
)
import logging

router = Router()

# ============================================================
# 1. Start Lookup
# ============================================================
@router.callback_query(F.data.in_({"rh_student_lookup", "dk_student_lookup", "tt_student_lookup"}))
async def start_student_lookup(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(StaffStudentLookupStates.waiting_input)
    
    await call.message.edit_text(
        "🔍 <b>Talaba qidirish</b>\n\n"
        "Talabaning <b>HEMIS ID</b> raqamini yoki <b>Ism-familiyasini</b> yozib yuboring.\n\n"
        "<i>Na'muna: 392211100444 yoki Olimov Anvar</i>",
        parse_mode="HTML",
        reply_markup=get_staff_student_lookup_back_kb()
    )
    await call.answer()


# ============================================================
# 2. Process Search Input
# ============================================================
@router.message(StaffStudentLookupStates.waiting_input)
async def process_lookup_input(message: Message, session: AsyncSession, state: FSMContext):
    query = message.text.strip()
    
    # Identify Staff
    staff = await session.scalar(
        select(Staff).join(TgAccount).where(TgAccount.telegram_id == message.from_user.id)
    )
    if not staff:
        await message.answer("❌ Xodim aniqlanmadi")
        return

    # Base Query
    stmt = select(Student).where(Student.university_id == staff.university_id)
    
    # Filter by Staff Role
    if staff.role == StaffRole.DEKANAT:
        stmt = stmt.where(Student.faculty_id == staff.faculty_id)
    elif staff.role == StaffRole.TYUTOR:
        # Load tutor groups
        staff_full = await session.get(Staff, staff.id, options=[selectinload(Staff.tutor_groups)])
        my_groups = [g.group_number for g in staff_full.tutor_groups]
        if not my_groups:
             await message.answer("⚠️ Sizga guruhlar biriktirilmagan.")
             return
        stmt = stmt.where(Student.group_number.in_(my_groups))
        
    # Apply Search Filter (HEMIS ID exact or Name partial)
    if query.isdigit() and len(query) > 9: # HEMIS ID length check roughly
        stmt = stmt.where(Student.hemis_login == query)
    else:
        stmt = stmt.where(Student.full_name.ilike(f"%{query}%"))
        
    students = (await session.scalars(stmt)).all()
    
    if not students:
        await message.answer(
            f"❌ <b>'{query}'</b> bo'yicha hech kim topilmadi.\n\n"
            "Sabablar bo'lishi mumkin:\n"
            "1. Talaba sizning fakultet/guruhingizga tegishli emas.\n"
            "2. HEMIS ID yoki ism noto'g'ri yozildi.\n"
            "3. Talaba bazada mavjud emas.\n\n"
            "Qayta urinib ko'ring:",
            parse_mode="HTML",
            reply_markup=get_staff_student_lookup_back_kb()
        )
        return
        
    if len(students) > 1:
        text = "🔍 <b>Qidiruv natijalari:</b>\n\n"
        for i, s in enumerate(students[:10], 1):
             text += f"{i}. <b>{s.full_name}</b> ({s.group_number}) - <code>{s.hemis_login}</code>\n"
             
        text += "\n⚠️ Iltimos, aniqroq qilib <b>HEMIS ID</b> kiriting."
        await message.answer(text, parse_mode="HTML", reply_markup=get_staff_student_lookup_back_kb())
        return

    # Single result found
    await show_student_profile(message, students[0], session)
    await state.clear() # Clear state acts as "done", actions are handled via callback


async def show_student_profile(message: Message, student: Student, session: AsyncSession):
    # Calculate Stats
    
    # Activities
    act_stats = await session.execute(
        select(UserActivity.status, func.count(UserActivity.id))
        .where(UserActivity.student_id == student.id)
        .group_by(UserActivity.status)
    )
    act_counts = dict(act_stats.all())
    approved = act_counts.get("confirmed", 0)
    rejected = act_counts.get("rejected", 0)
    pending = act_counts.get("pending", 0)
    
    # Appeals
    appeal_count = await session.scalar(
        select(func.count(StudentFeedback.id)).where(StudentFeedback.student_id == student.id)
    )

    # Faculty Name Fetch
    faculty_name = "---"
    if student.faculty_id:
        faculty = await session.get(Faculty, student.faculty_id)
        if faculty:
            faculty_name = faculty.name

    text = (
        f"🎓 <b>TALABA PROFILI</b>\n\n"
        f"👤 <b>{student.full_name}</b>\n"
        f"🆔 HEMIS: <code>{student.hemis_login}</code>\n"
        f"🏫 Fakultet: {faculty_name}\n"
        f"👥 Guruh: {student.group_number or '---'}\n"
        f"📞 Telefon: {student.phone or 'Tasdiqlanmagan'}\n"
        f"⭐️ GPA: ---\n\n"
        f"📊 <b>Faolliklar:</b>\n"
        f"✅ Tasdiqlangan: <b>{approved}</b>\n"
        f"❌ Rad etilgan: <b>{rejected}</b>\n"
        f"⏳ Kutilmoqda: <b>{pending}</b>\n\n"
        f"📨 Murojaatlar soni: <b>{appeal_count}</b>"
    )
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_student_profile_actions_kb(student.id)
    )


@router.callback_query(F.data.in_({"staff_profile_back", "go_home"}))
async def back_from_profile(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.message.delete()
    await state.clear() # Clear specific student lookup state
    
    # Get staff role to decide which menu
    staff = await session.scalar(select(Staff).join(TgAccount).where(TgAccount.telegram_id == call.from_user.id))
    
    if not staff:
        # Fallback
        await call.message.answer("Bosh sahifaga qaytish", reply_markup=get_staff_student_lookup_back_kb())
        return

    if staff.role == StaffRole.RAHBARIYAT:
        kb = get_rahbariyat_main_menu_kb()
        text = "🏢 Rahbariyat paneli"
    elif staff.role == StaffRole.DEKANAT:
        kb = get_dekanat_main_menu_kb()
        text = "🏛 Dekanat paneli"
    elif staff.role == StaffRole.TYUTOR:
        kb = get_tutor_main_menu_kb()
        text = "🎓 Tyutor paneli"
    else:
        # Fallback or error
        kb = get_staff_student_lookup_back_kb()
        text = "Bosh sahifa"

    await call.message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("staff_back_to_profile:"))
async def back_to_profile_handler(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    student_id = int(call.data.split(":")[1])
    # Recalculate usage of show_student_profile
    # We need to fetch student first
    student = await session.get(Student, student_id)
    if not student:
        await call.answer("Talaba topilmadi")
        return
        
    await call.message.delete()
    await show_student_profile(call.message, student, session)



# ============================================================
# 3. Direct Message to Student
# ============================================================
from models.states import RequestSimpleStates # or similar simple state

@router.callback_query(F.data.startswith("staff_send_msg:"))
async def staff_send_msg_start(call: CallbackQuery, state: FSMContext):
    student_id = int(call.data.split(":")[1])
    await state.update_data(target_student_id=student_id)
    
    # Use proper state
    await state.set_state(StaffStudentLookupStates.sending_message)
    
    await call.message.answer(
        "📝 <b>Talabaga xabar yozing yoki fayl yuboring:</b>\n"
        "Xabar bot nomidan yuboriladi.",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(StaffStudentLookupStates.sending_message)
async def staff_send_msg_process(message: Message, session: AsyncSession, state: FSMContext):
    logging.info(f"Entered staff_send_msg_process for user {message.from_user.id}")
    data = await state.get_data()
    student_id = data.get("target_student_id")
    
    if not student_id:
        await message.answer("❌ Xatolik: Talaba aniqlanmadi (sessiya eskirgan).")
        await state.clear()
        return

    student = await session.get(Student, student_id)
    if not student:
        await message.answer("❌ Talaba bazada topilmadi.")
        await state.clear()
        return

    tg = await session.scalar(select(TgAccount).where(TgAccount.student_id == student_id))
    
    if tg:
        try:
            # Get Staff info for signature
            staff = await session.scalar(select(Staff).join(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
            
            if staff:
                # Format role nice or use position if available
                if staff.position:
                    staff_name = f"{staff.position} {staff.full_name}"
                else:
                    role_val = staff.role.value if hasattr(staff.role, "value") else str(staff.role)
                    role_display = role_val.capitalize()
                    staff_name = f"{role_display} {staff.full_name}"
            else:
                staff_name = "Xodim"

            caption_header = (
                 f"📨 <b>Xodimdan xabar:</b>\n\n"
                 f"👤 <b>{staff_name}</b>\n"
            )
            
            input_text = message.text or message.caption or ""
            full_msg = caption_header + f"<i>{input_text}</i>"
            
            # Send logic
            if message.photo:
                await message.bot.send_photo(tg.telegram_id, message.photo[-1].file_id, caption=full_msg, parse_mode="HTML")
            elif message.document:
                 await message.bot.send_document(tg.telegram_id, message.document.file_id, caption=full_msg, parse_mode="HTML")
            elif message.video:
                 await message.bot.send_video(tg.telegram_id, message.video.file_id, caption=full_msg, parse_mode="HTML")
            elif input_text:
                await message.bot.send_message(tg.telegram_id, full_msg, parse_mode="HTML")
            else:
                await message.answer("⚠️ Matn yoki fayl kiritilmadi.")
                return

            # Success message to Staff with Profile Button
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Talaba profiliga qaytish", callback_data=f"staff_back_to_profile:{student_id}")]
            ])
            await message.answer(f"✅ Xabar <b>{student.full_name}</b> ga yuborildi.", parse_mode="HTML", reply_markup=kb)
            
        except Exception as e:
            await message.answer(f"❌ Yuborishda xatolik: {e}")
            logging.error(f"Failed to send DM to student {student_id}: {e}")
    else:
        await message.answer("❌ Talabaning Telegrami ulanmagan.")
        
    await state.clear()



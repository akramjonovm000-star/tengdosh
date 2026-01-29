"""
Tyutor ishlarini (6 yo'nalish) tasdiqlash uchun handlerlar.
Rahbariyat va Dekanat uchun.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import TyutorWorkLog, Staff, StaffRole, TgAccount, Student, Faculty

router = Router()

# State
from aiogram.fsm.state import StatesGroup, State

class TyutorWorkApproveStates(StatesGroup):
    reviewing = State()


# Helpers
async def get_staff_from_tg(user_id: int, session: AsyncSession):
    return await session.scalar(
        select(Staff).join(TgAccount).where(TgAccount.telegram_id == user_id)
    )

def get_work_review_kb(log_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tw_approve:{log_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tw_reject:{log_id}")
        ],
        [
            InlineKeyboardButton(text="➡️ Keyingisi", callback_data="tw_next")
        ],
        [
            InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="tw_back")
        ]
    ])


@router.callback_query(F.data.in_({"rahb_tyutor_works", "dek_tyutor_works"}))
async def start_tyutor_works_review(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Tyutor ishlarini ko'rib chiqishni boshlash"""
    staff = await get_staff_from_tg(call.from_user.id, session)
    if not staff:
        await call.answer("Xodim topilmadi", show_alert=True)
        return

    # Base query
    stmt = select(TyutorWorkLog).where(TyutorWorkLog.status == "pending")
    
    # Filter by role
    if staff.role == StaffRole.DEKANAT:
        # Faqat o'z fakulteti tyutorlari
        # Tyutor -> Faculty
        # TyutorWorkLog -> Staff (Tyutor) -> Faculty
        stmt = stmt.join(Staff).where(Staff.faculty_id == staff.faculty_id)
    elif staff.role == StaffRole.RAHBARIYAT:
        pass # All
    else:
        await call.answer("Ruxsatsiz kirish", show_alert=True)
        return
    
    stmt = stmt.order_by(TyutorWorkLog.created_at)
    logs = (await session.scalars(stmt)).all()
    
    if not logs:
        text = "📭 Tasdiqlash uchun yangi tyutor ishlari yo'q."
        # Back button based on role
        if staff.role == StaffRole.RAHBARIYAT:
            back_cb = "rahb_menu" # Assumed callback
        else:
            back_cb = "dek_menu" # Assumed callback
            
        await call.message.edit_text(
            text, 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                 InlineKeyboardButton(text="🏠 Bosh menyu", callback_data=back_cb)
            ]])
        )
        return
    
    # Start reviewing
    await state.set_state(TyutorWorkApproveStates.reviewing)
    await state.update_data(log_ids=[l.id for l in logs], index=0)
    
    await send_work_review(call.message, logs[0], session)


async def send_work_review(message: Message, work: TyutorWorkLog, session: AsyncSession):
    tyutor = await session.get(Staff, work.tyutor_id)
    
    student_name = "--- (Umumiy)"
    if work.student_id:
        student = await session.get(Student, work.student_id)
        if student:
            student_name = f"{student.full_name} ({student.group_number})"
    
    caption = (
        f"📋 <b>Tyutor Ishi #{work.id}</b>\n\n"
        f"🧑‍🏫 Tyutor: <b>{tyutor.full_name} ({tyutor.faculty.name if tyutor.faculty else ''})</b>\n"
        f"👤 Talaba: {student_name}\n"
        f"📂 Yo'nalish: <b>{work.direction_type}</b>\n\n"
        f"🏷 Nomi: {work.title or '---'}\n"
        f"📝 Tavsif: {work.description or '---'}\n"
        f"📅 Sana: {work.completion_date or '---'}\n"
    )
    
    kb = get_work_review_kb(work.id)
    
    if work.file_id:
        if work.file_type == "photo":
            await message.answer_photo(work.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
        elif work.file_type == "document":
            await message.answer_document(work.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=kb)

    # Note: If message was edited, we'd delete the old one, but here we can just send new message for photos
    # Proper way is deleting previous if we want carousel feel, but keeping it simple for now.


@router.callback_query(F.data.startswith("tw_approve:"))
async def approve_tyutor_work(call: CallbackQuery, session: AsyncSession):
    log_id = int(call.data.split(":")[1])
    
    log = await session.get(TyutorWorkLog, log_id)
    if log:
        log.status = "confirmed"
        log.points = 5 # Fixed points
        await session.commit()
        await call.answer("✅ Tasdiqlandi (+5 ball)")
        await call.message.edit_reply_markup(reply_markup=None) # Remove buttons
    else:
        await call.answer("Xatolik: Ish topilmadi", show_alert=True)


@router.callback_query(F.data.startswith("tw_reject:"))
async def reject_tyutor_work(call: CallbackQuery, session: AsyncSession):
    log_id = int(call.data.split(":")[1])
    
    log = await session.get(TyutorWorkLog, log_id)
    if log:
        log.status = "rejected"
        log.points = 0
        await session.commit()
        await call.answer("❌ Rad etildi")
        await call.message.edit_reply_markup(reply_markup=None)
    else:
        await call.answer("Xatolik: Ish topilmadi", show_alert=True)


@router.callback_query(F.data == "tw_next")
async def next_tyutor_work(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    ids = data.get("log_ids", [])
    idx = data.get("index", 0)
    
    new_idx = idx + 1
    if new_idx >= len(ids):
        await call.answer("Boshqa ish qolmadi", show_alert=True)
        await state.clear()
        # Redirect to menu maybe?
        return

    await state.update_data(index=new_idx)
    log = await session.get(TyutorWorkLog, ids[new_idx])
    
    if log:
        await call.message.delete() # Clean up old
        await send_work_review(call.message, log, session)
        await call.answer()
    else:
        # Skip if deleted
        await next_tyutor_work(call, session, state)


@router.callback_query(F.data == "tw_back")
async def back_to_menu_tw(call: CallbackQuery):
    await call.message.delete()
    # Should probably send the main menu again, but for now just delete.
    await call.answer("Menyuga qaytilmoqda")

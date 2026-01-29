from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Staff, TgAccount, StaffRole
from keyboards.inline_kb import (
    get_staff_role_select_kb,
    get_rahbariyat_main_menu_kb as get_rahbariyat_main_menu,
    get_dekanat_main_menu_kb,
    get_tutor_main_menu_kb,
)

from models.states import StaffAuthStates

router = Router()


# =========================================
# 1) Xodim bo‘limi - rol tanlash
# =========================================
@router.callback_query(F.data == "staff_menu")
async def staff_menu(call: CallbackQuery):
    from config import DOMAIN
    oauth_url = f"https://{DOMAIN}/api/v1/oauth/login?source=staff_bot"
    kb = get_staff_role_select_kb()
    # Prepend or Modify KB via code, or just rely on get_staff_role_select_kb update?
    # I didn't update inline_kb.py because it's shared.
    # Let's do it here explicitly to avoid side effects.
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 HEMIS orqali kirish (Tavsiya)", url=oauth_url)],
            *kb.inline_keyboard
        ]
    )
    
    await call.message.edit_text(
        "👨‍💼 Xodim sifatida tizimga kirish uchun usulni tanlang:",
        reply_markup=kb
    )
    await call.answer()


# =========================================
# 2) ROL tanlanganda JSHSHIR so‘raymiz
# =========================================
@router.callback_query(F.data.startswith("staff_role_"))
async def staff_role_selected(call: CallbackQuery, state: FSMContext):

    selected_role = call.data.replace("staff_role_", "")  # rahbariyat / dekanat / tyutor

    await state.set_state(StaffAuthStates.entering_jshshir)
    await state.update_data(expected_role=selected_role)

    await call.message.edit_text(
        f"🔑 <b>{selected_role.capitalize()}</b> sifatida kirish uchun JSHSHIR kiriting:",
        parse_mode="HTML"
    )
    await call.answer()


# =========================================
# 3) Xodim JSHSHIR yuboradi → DB tekshiramiz
# =========================================
@router.message(StaffAuthStates.entering_jshshir)
async def staff_jshshir_entered(message: Message, state: FSMContext, session: AsyncSession):

    jshshir = message.text.strip()
    data = await state.get_data()
    expected_role = data.get("expected_role")

    # Xodimni qidiramiz
    staff = await session.scalar(
        select(Staff).where(Staff.jshshir == jshshir)
    )

    if not staff:
        await message.answer("❌ Bunday JSHSHIR topilmadi. Qayta urinib ko‘ring.")
        return

    if staff.role.value != expected_role:
        await message.answer(
            f"❌ Sizning rolingiz <b>{staff.role.value}</b>.\n"
            f"Bu bo‘limga kirish uchun <b>{expected_role}</b> bo‘lishingiz kerak.",
            parse_mode="HTML"
        )
        return

    # TG account bilan bog‘laymiz
    tg_account = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == message.from_user.id)
    )

    if not tg_account:
        tg_account = TgAccount(
            telegram_id=message.from_user.id,
            staff_id=staff.id,
            current_role=staff.role.value
        )
        session.add(tg_account)
    else:
        tg_account.staff_id = staff.id
        tg_account.current_role = staff.role.value

    await session.commit()
    await state.clear()

    # To‘g‘ri menyuga yo‘naltiramiz
    if staff.role == StaffRole.RAHBARIYAT:
        await message.answer(
            "🏛 Rahbariyat menyusiga xush kelibsiz!",
            reply_markup=get_rahbariyat_main_menu()
        )

    elif staff.role == StaffRole.DEKANAT:
        await message.answer(
            "🏫 Dekanat menyusiga xush kelibsiz!",
            reply_markup=get_dekanat_main_menu_kb()
        )

    elif staff.role == StaffRole.TYUTOR:
        await message.answer(
            "👨‍🏫 Tyutor menyusiga xush kelibsiz!",
            reply_markup=get_tutor_main_menu_kb()
        )
        
    # ----------------------------------------
    # DELIVER PENDING APPEALS
    # ----------------------------------------
    try:
        from database.models import StudentFeedback, Student
        from keyboards.inline_kb import get_staff_appeal_actions_kb
        
        pending_feedbacks = await session.scalars(
            select(StudentFeedback).where(
                StudentFeedback.assigned_staff_id == staff.id,
                StudentFeedback.status != "closed"
            ).order_by(StudentFeedback.created_at.asc())
        )
        feedbacks = pending_feedbacks.all()
        
        if feedbacks:
            await message.answer(f"📨 <b>Sizda {len(feedbacks)} ta o'qilmagan murojaat bor:</b>", parse_mode="HTML")
            
            for fb in feedbacks:
                student = await session.get(Student, fb.student_id)
                if not student: continue
                
                sender_name = "Anonim" if fb.is_anonymous else f"{student.full_name} ({student.group_number})"
                caption = f"📨 <b>Eski murojaat</b>\n\nKimdan: {sender_name}\n\n"
                if fb.text: caption += f"Matn: {fb.text}\n"
                caption += f"📅 Sana: {fb.created_at.strftime('%d.%m.%Y %H:%M')}"
                
                kb = get_staff_appeal_actions_kb(fb.id, role=staff.role.value, student_id=student.id if not fb.is_anonymous else None)
                
                try:
                    if fb.file_type == "photo":
                        await message.bot.send_photo(message.from_user.id, fb.file_id, caption=caption[:1000], reply_markup=kb, parse_mode="HTML")
                    elif fb.file_type == "document":
                        await message.bot.send_document(message.from_user.id, fb.file_id, caption=caption[:1000], reply_markup=kb, parse_mode="HTML")
                    elif fb.file_type == "video":
                        await message.bot.send_video(message.from_user.id, fb.file_id, caption=caption[:1000], reply_markup=kb, parse_mode="HTML")
                    else:
                        await message.bot.send_message(message.from_user.id, caption, reply_markup=kb, parse_mode="HTML")
                except Exception as e:
                    pass
                    
    except Exception as e:
        print(f"Error delivering pending appeals: {e}")

import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Staff, StaffRole, Student
from models.states import OwnerGifts
from keyboards.inline_kb import get_back_inline_kb
from config import OWNER_TELEGRAM_ID

router = Router()
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# CHECK OWNER PERMISSION
# -------------------------------------------------------------
async def _is_owner(user_id: int, session: AsyncSession) -> bool:
    if user_id == OWNER_TELEGRAM_ID:
        return True
    
    result = await session.execute(
        select(Staff).where(
            Staff.telegram_id == user_id,
            Staff.role == StaffRole.OWNER,
            Staff.is_active == True
        )
    )
    return result.scalar_one_or_none() is not None

# -------------------------------------------------------------
# 1. MENU: Premium Options
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_gifts_menu")
async def cb_owner_gifts_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await _is_owner(call.from_user.id, session):
        return await call.answer("❌ Ruxsat yo'q", show_alert=True)

    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Premium sovg'a qilish", callback_data="owner_gift_start")],
        [InlineKeyboardButton(text="📢 Barchaga Premium sovg'a qilish", callback_data="owner_gift_all_start")],
        [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="owner_topup_start")],
        [InlineKeyboardButton(text="❌ Premium to'xtatish", callback_data="owner_revoke_start")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_menu")]
    ])

    await call.message.edit_text(
        "💎 <b>Premium boshqaruvi</b>\n\n"
        "Foydalanuvchilarga Premium berish yoki uni bekor qilish uchun quyidagilardan birini tanlang.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# -------------------------------------------------------------
# 2. GIVE PREMIUM: ASK USER ID
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_gift_start")
async def cb_gift_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerGifts.waiting_user_id)
    
    await call.message.edit_text(
        "👤 <b>Premium berish:</b>\n"
        "Foydalanuvchi ID sini yoki loginini kiriting:",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    await call.answer()

# -------------------------------------------------------------
# 2.1 REVOKE PREMIUM: ASK USER ID
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_revoke_start")
async def cb_revoke_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerGifts.waiting_revoke_id)
    
    await call.message.edit_text(
        "👤 <b>Premium to'xtatish:</b>\n"
        "Foydalanuvchi ID sini yoki loginini kiriting:",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    await call.answer()

# -------------------------------------------------------------
# 2.2 TOP UP BALANCE START
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_topup_start")
async def cb_topup_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerGifts.waiting_topup_hemis_id)
    
    await call.message.edit_text(
        "💰 <b>Balansni to'ldirish:</b>\n"
        "Foydalanuvchi HEMIS ID yoki loginini kiriting:",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    await call.answer()

# -------------------------------------------------------------
# 3. PROCESS USER ID (FOR GIFTING)
# -------------------------------------------------------------
@router.message(OwnerGifts.waiting_user_id)
async def msg_process_user_id(message: Message, state: FSMContext, session: AsyncSession):
    raw_id = message.text.strip()
    
    # Search logic
    user = await session.scalar(select(User).where(User.hemis_id == raw_id))
    if not user:
        user = await session.scalar(select(User).where(User.hemis_login == raw_id))
    if not user and raw_id.isdigit():
        user = await session.scalar(select(User).where(User.id == int(raw_id)))
        
    if not user:
        await message.answer(
            "❌ Foydalanuvchi topilmadi.\n"
            "Iltimos, to'g'ri ID yoki Login kiriting.",
            reply_markup=get_back_inline_kb("owner_gifts_menu"),
            parse_mode="HTML"
        )
        return

    student = await session.scalar(select(Student).where(Student.hemis_login == user.hemis_login))
    student_id = student.id if student else None
    
    await state.update_data(
        target_user_id=user.id, 
        target_student_id=student_id,
        target_name=user.full_name
    )
    await state.set_state(OwnerGifts.selecting_duration)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 3 kun", callback_data="gift_dur_3d")],
        [InlineKeyboardButton(text="📅 Bir hafta", callback_data="gift_dur_7d")],
        [InlineKeyboardButton(text="📅 10 kun", callback_data="gift_dur_10d")],
        [InlineKeyboardButton(text="📅 Bir oy", callback_data="gift_dur_1m")],
        [InlineKeyboardButton(text="📅 Uch oy", callback_data="gift_dur_3m")],
        [InlineKeyboardButton(text="📅 Bir yil", callback_data="gift_dur_1y")],
        [InlineKeyboardButton(text="♾ Doimiy (Lifetime)", callback_data="gift_dur_life")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="owner_gifts_menu")]
    ])
    
    await message.answer(
        f"✅ <b>Foydalanuvchi topildi:</b> {user.full_name}\n\n"
        f"⏳ premium muddatini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# -------------------------------------------------------------
# 3.1 PROCESS USER ID (FOR REVOKING)
# -------------------------------------------------------------
@router.message(OwnerGifts.waiting_revoke_id)
async def msg_process_revoke_id(message: Message, state: FSMContext, session: AsyncSession):
    raw_id = message.text.strip()
    
    # Search logic
    user = await session.scalar(select(User).where(User.hemis_id == raw_id))
    if not user:
        user = await session.scalar(select(User).where(User.hemis_login == raw_id))
    if not user and raw_id.isdigit():
        user = await session.scalar(select(User).where(User.id == int(raw_id)))
        
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi.", reply_markup=get_back_inline_kb("owner_gifts_menu"))
        return

    student = await session.scalar(select(Student).where(Student.hemis_login == user.hemis_login))
    
    # Revoke Prem
    user.is_premium = False
    user.premium_expiry = None
    if student:
        student.is_premium = False
        student.premium_expiry = None
        
        from database.models import StudentNotification
        notification = StudentNotification(
            student_id=student.id,
            title="⚠️ Premium muddati tugadi",
            body="Sizning Premium obunangiz to'xtatildi yoki muddati tugadi. Imkoniyatlarni qayta tiklash uchun hisobingizni to'ldiring.",
            type="alert"
        )
        session.add(notification)
        
    await session.commit()
    
    await message.answer(
        f"✅ <b>{user.full_name}</b> dan Premium olib tashlandi.",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    await state.clear()

# -------------------------------------------------------------
# 4. PROCESS DURATION & GIVE PREMIUM
# -------------------------------------------------------------
@router.callback_query(OwnerGifts.selecting_duration, F.data.startswith("gift_dur_"))
async def cb_process_duration(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    duration_code = call.data.split("_")[2] # 1m, 3m, 6m, 1y, life
    
    data = await state.get_data()
    user_id = data.get("target_user_id")
    student_id = data.get("target_student_id")
    name = data.get("target_name")
    
    user = await session.get(User, user_id)
    if not user:
         await call.message.edit_text("❌ Xatolik: User topilmadi.", reply_markup=get_back_inline_kb("owner_gifts_menu"))
         return

    now = datetime.utcnow()
    expiry_date = None
    duration_text = ""
    
    if duration_code == "3d":
        expiry_date = now + timedelta(days=3)
        duration_text = "3 kun"
    elif duration_code == "7d":
        expiry_date = now + timedelta(days=7)
        duration_text = "Bir hafta"
    elif duration_code == "10d":
        expiry_date = now + timedelta(days=10)
        duration_text = "10 kun"
    elif duration_code == "1m":
        expiry_date = now + timedelta(days=30)
        duration_text = "Bir oy"
    elif duration_code == "3m":
        expiry_date = now + timedelta(days=90)
        duration_text = "Uch oy"
    elif duration_code == "6m":
        expiry_date = now + timedelta(days=180)
        duration_text = "Olti oy"
    elif duration_code == "1y":
        expiry_date = now + timedelta(days=365)
        duration_text = "Bir yil"
    elif duration_code == "life":
        expiry_date = now + timedelta(days=365*100)
        duration_text = "Doimiy"
        
    user.is_premium = True
    user.premium_expiry = expiry_date
    
    student = None
    if student_id:
        student = await session.get(Student, student_id)
        if student:
            student.is_premium = True
            student.premium_expiry = expiry_date
            
            from database.models import StudentNotification
            notification = StudentNotification(
                student_id=student.id,
                title="🎁 Premium sovg'a qilindi!",
                body=f"Tabriklaymiz! Sizga {duration_text} muddatga Premium obuna sovg'a qilindi.",
                type="success"
            )
            session.add(notification)
    
    await session.commit()
    
    await call.message.edit_text(
        f"✅ <b>Premium berildi!</b>\n👤 {name}\n⏳ {duration_text}",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    
    # Notification logic
    try:
        if student:
            from database.models import TgAccount
            tg_acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
            if tg_acc:
                msg = f"🎉 <b>Sizga {duration_text} muddatga Premium sovg'a qilindi!</b>"
                await call.bot.send_message(tg_acc.telegram_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not notify user: {e}")
        
    await state.clear()
    await call.answer()

# -------------------------------------------------------------
# 4.1 GIFT TO ALL START
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_gift_all_start")
async def cb_gift_all_start(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await _is_owner(call.from_user.id, session):
        return await call.answer("❌ Ruxsat yo'q", show_alert=True)

    await state.set_state(OwnerGifts.selecting_duration_all)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 3 kun", callback_data="gift_all_dur_3d")],
        [InlineKeyboardButton(text="📅 Bir hafta", callback_data="gift_all_dur_7d")],
        [InlineKeyboardButton(text="📅 10 kun", callback_data="gift_all_dur_10d")],
        [InlineKeyboardButton(text="📅 Bir oy", callback_data="gift_all_dur_1m")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="owner_gifts_menu")]
    ])
    
    await call.message.edit_text(
        "📢 <b>Barcha foydalanuvchilarga Premium berish</b>\n\n"
        "Barcha login qilgan talabalarga premium beriladi. Muddatni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# -------------------------------------------------------------
# 4.2 PROCESS DURATION ALL & GIVE PREMIUM
# -------------------------------------------------------------
@router.callback_query(OwnerGifts.selecting_duration_all, F.data.startswith("gift_all_dur_"))
async def cb_process_duration_all(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    duration_code = call.data.split("_")[3] # 3d, 7d, 10d, 1m
    
    now = datetime.utcnow()
    expiry_date = None
    duration_text = ""
    
    if duration_code == "3d":
        expiry_date = now + timedelta(days=3)
        duration_text = "3 kun"
    elif duration_code == "7d":
        expiry_date = now + timedelta(days=7)
        duration_text = "Bir hafta"
    elif duration_code == "10d":
        expiry_date = now + timedelta(days=10)
        duration_text = "10 kun"
    elif duration_code == "1m":
        expiry_date = now + timedelta(days=30)
        duration_text = "Bir oy"
        
    # Bulk Update Students
    from sqlalchemy import update as sa_update
    from database.models import StudentNotification
    
    # 1. Update Students
    stmt_student = sa_update(Student).values(
        is_premium=True,
        premium_expiry=expiry_date
    )
    await session.execute(stmt_student)
    
    # 2. Update Users (if they have is_premium field)
    stmt_user = sa_update(User).values(
        is_premium=True,
        premium_expiry=expiry_date
    )
    await session.execute(stmt_user)
    
    # 3. Add notifications (This part is tricky for ALL users, usually we don't insert 50k rows. 
    # Better to send a global broadcast via a service later, but user requested 'barcha login qilganlarga'.
    # For now, let's at least perform the bulk update. The app's profile screen checks the DB anyway.)
    
    await session.commit()
    
    # 4. Trigger Global Broadcast in background
    try:
        from services.notification_service import NotificationService
        NotificationService.run_broadcast.delay(
            title="🎁 Barchaga Premium sovg'a!",
            body=f"Ma'muriyat tomonidan barcha foydalanuvchilarga {duration_text} muddatga Premium obuna taqdim etildi! 🎉",
            data={"type": "premium_gift"}
        )
    except Exception as e:
        logger.error(f"Global broadcast failed: {e}")

    await call.message.edit_text(
        f"✅ <b>Barchaga Premium berildi!</b>\n⏳ Muddat: {duration_text}\n\n"
        f"Xabar tarqatish jarayoni fonda boshlandi.",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    
    await state.clear()
    await call.answer()


# -------------------------------------------------------------
# 5. TOP UP BALANCE LOGIC
# -------------------------------------------------------------

@router.message(OwnerGifts.waiting_topup_hemis_id)
async def msg_process_topup_id(message: Message, state: FSMContext, session: AsyncSession):
    raw_id = message.text.strip()
    
    # Search logic (Reuse similarity)
    user = await session.scalar(select(User).where(User.hemis_id == raw_id))
    if not user:
        user = await session.scalar(select(User).where(User.hemis_login == raw_id))
    if not user and raw_id.isdigit():
        user = await session.scalar(select(User).where(User.id == int(raw_id)))
        
    if not user:
        await message.answer(
            "❌ Foydalanuvchi topilmadi.\n"
            "Iltimos, to'g'ri ID yoki Login kiriting.",
            reply_markup=get_back_inline_kb("owner_gifts_menu"),
            parse_mode="HTML"
        )
        return

    # Check student
    student = await session.scalar(select(Student).where(Student.hemis_login == user.hemis_login))
    if not student:
         await message.answer(
            "❌ Bu foydalanuvchi talaba emas (Student jadvalida yo'q).\n"
            "Balans faqat talabalar uchun.",
            reply_markup=get_back_inline_kb("owner_gifts_menu")
        )
         return
    
    await state.update_data(
        target_user_id=user.id,
        target_student_id=student.id,
        target_name=user.full_name,
        current_balance=student.balance
    )
    
    await state.set_state(OwnerGifts.waiting_topup_amount)
    await message.answer(
        f"✅ <b>Foydalanuvchi topildi:</b> {user.full_name}\n"
        f"💰 Hozirgi balans: {student.balance} so'm\n\n"
        "Qancha summa qo'shmoqchisiz? (faqat raqam, masalan: 50000)",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )


@router.message(OwnerGifts.waiting_topup_amount)
async def msg_process_topup_amount(message: Message, state: FSMContext, session: AsyncSession):
    amount_str = message.text.strip().replace(" ", "")
    
    if not amount_str.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting (masalan: 10000)")
        return

    amount = int(amount_str)
    if amount <= 0:
        await message.answer("❌ Summa musbat bo'lishi kerak.")
        return

    data = await state.get_data()
    student_id = data.get("target_student_id")
    name = data.get("target_name")
    
    student = await session.get(Student, student_id)
    if not student:
        await message.answer("❌ Talaba topilmadi.")
        await state.clear()
        return

    # Update Balance
    old_balance = student.balance
    student.balance += amount
    await session.commit()
    
    # Notify Student
    from database.models import StudentNotification, TgAccount
    
    notification = StudentNotification(
        student_id=student.id,
        title="💰 Balansingiz to'ldirildi",
        body=f"Hisobingizga {amount} so'm muvaffaqiyatli o'tkazildi.\nJoriy balans: {student.balance} so'm.",
        type="success"
    )
    session.add(notification)
    await session.commit()

    # Try Telegram Notify
    try:
        tg_acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
        if tg_acc:
            msg = (
                f"💰 <b>Balans to'ldirildi!</b>\n\n"
                f"Sizning hisobingizga {amount} so'm qo'shildi.\n"
                f"Joriy balans: {student.balance} so'm."
            )
            await message.bot.send_message(tg_acc.telegram_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not notify user via TG: {e}")

    await message.answer(
        f"✅ <b>Balans yangilandi!</b>\n\n"
        f"👤 {name}\n"
        f"➕ Qo'shildi: {amount} so'm\n"
        f"💰 Yangi balans: {student.balance} so'm",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    await state.clear()

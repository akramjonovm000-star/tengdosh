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
from config import DEVELOPERS, OWNER_TELEGRAM_ID

router = Router()
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# CHECK OWNER PERMISSION
# -------------------------------------------------------------
async def _is_owner(user_id: int, session: AsyncSession) -> bool:
    if user_id in DEVELOPERS:
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
    
    student = await session.scalar(select(Student).where(Student.hemis_id == raw_id))
    if not student and raw_id.isdigit():
        student = await session.scalar(select(Student).where(Student.id == int(raw_id)))
        
    staff = None
    if not student:
        staff = await session.scalar(select(Staff).where(Staff.employee_id_number == raw_id))
        if not staff and raw_id.isdigit():
             staff = await session.scalar(select(Staff).where(Staff.id == int(raw_id)))
             
    if not student and not staff:
        await message.answer("❌ Foydalanuvchi topilmadi.\nIltimos, to'g'ri ID kiriting.", reply_markup=get_back_inline_kb("owner_gifts_menu"), parse_mode="HTML")
        return

    target_name = student.full_name if student else staff.full_name
    current_balance = student.balance if student else staff.balance
    
    await state.update_data(
        target_student_id=student.id if student else None,
        target_staff_id=staff.id if staff else None,
        target_name=target_name,
        current_balance=current_balance
    )
    
    await state.set_state(OwnerGifts.waiting_topup_amount)
    await message.answer(
        f"✅ <b>Foydalanuvchi topildi:</b> {target_name}\n"
        f"💰 Hozirgi balans: {current_balance} so'm\n\n"
        "Qancha summa qo'shmoqchisiz? (faqat raqam, masalan: 50000)",
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
    student_id = data.get("target_student_id")
    staff_id = data.get("target_staff_id")
    name = data.get("target_name")
    
    student = None
    staff = None
    
    if student_id:
        student = await session.get(Student, student_id)
    if staff_id:
        staff = await session.get(Staff, staff_id)
        
    if not student and not staff:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        await state.clear()
        return

    from database.models import StudentNotification, TgAccount
    
    if student:
        student.balance += amount
        notification = StudentNotification(student_id=student.id, title="💰 Balansingiz to'ldirildi", body=f"Hisobingizga {amount} so'm muvaffaqiyatli o'tkazildi.\nJoriy balans: {student.balance} so'm.", type="success")
        session.add(notification)
        current_balance = student.balance
    if staff:
        staff.balance += amount
        current_balance = staff.balance
        
    await session.commit()
    
    await call.message.edit_text(
        f"✅ <b>Premium berildi!</b>\n👤 {name}\n⏳ {duration_text}",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    
    # Notification logic
    try:
        tg_acc = None
        if student:
            tg_acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
        elif staff:
            tg_acc = await session.scalar(select(TgAccount).where(TgAccount.staff_id == staff.id))
            
        if tg_acc:
            msg = f"🎉 <b>Sizga {duration_text} muddatga Premium sovg'a qilindi!</b>"
            await call.bot.send_message(tg_acc.telegram_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not notify user: {e}")
        
    await state.clear()
    await call.answer()

# -------------------------------------------------------------
# MULTI-SELECT HELPER FUNCTIONS
# -------------------------------------------------------------
def build_multiselect_kb(items: list[str], selected: list[str], prefix: str, next_action: str) -> InlineKeyboardMarkup:
    """
    Builds a vertical keyboard with ✅ toggles for selecting options.
    items: List of distinct strings (e.g., University names).
    selected: List of currently selected strings.
    prefix: Callback prefix for toggling, e.g., 'gift_uni_' -> 'gift_uni_INDEX'
    """
    keyboard = []
    
    # We map options by index to save callback data space
    for idx, item_name in enumerate(items):
        icon = "✅" if item_name in selected else "◻️"
        # We pass idx to avoid long callback_data limits. The handler must look up `items[idx]`.
        keyboard.append([InlineKeyboardButton(text=f"{icon} {item_name}", callback_data=f"{prefix}{idx}")])
        
    # Navigation row
    action_row = []
    if selected:
        action_row.append(InlineKeyboardButton(text=f"✅ Tanlandi ({len(selected)}) - Keyingisi ➡", callback_data=next_action))
    else:
        action_row.append(InlineKeyboardButton(text="Barchasi (Tanlamasdan) - Keyingisi ➡", callback_data=next_action))
        
    keyboard.append(action_row)
    keyboard.append([InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="owner_gifts_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# -------------------------------------------------------------
# 4.1 GIFT TO ALL START - SELECT UNIVERSITIES (STEP 1)
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_gift_all_start")
async def cb_gift_all_start(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await _is_owner(call.from_user.id, session):
        return await call.answer("❌ Ruxsat yo'q", show_alert=True)

    # Fetch all distinct universities from active students
    # Use Student table since we are gifting to students
    stmt = select(Student.university_name).where(Student.university_name.isnot(None)).distinct().order_by(Student.university_name)
    rows = await session.execute(stmt)
    universities = [r[0] for r in rows.all()]

    await state.update_data(
        gift_all_universities=universities, # Keep the mapping
        gift_all_selected_unis=[],
        gift_all_selected_faculties=[],
        gift_all_selected_specialties=[]
    )
    
    await state.set_state(OwnerGifts.selecting_universities_all)
    
    kb = build_multiselect_kb(
        items=universities, 
        selected=[], 
        prefix="gift_uni_", 
        next_action="gift_step_faculties"
    )
    
    await call.message.edit_text(
        "📢 <b>Barchaga Premium berish - Filtr (1/4)</b>\n\n"
        "Qaysi Universitet(lar) uchun premium bermoqchisiz?\n"
        "<i>Barchasini tanlash uchun shunchaki \"Keyingisi\" tugmasini bosing.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(OwnerGifts.selecting_universities_all, F.data.startswith("gift_uni_"))
async def cb_toggle_university(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    idx = int(call.data.split("_")[2])
    data = await state.get_data()
    
    universities = data.get("gift_all_universities", [])
    selected = data.get("gift_all_selected_unis", [])
    
    if idx >= len(universities):
        return await call.answer("Xatolik: Ro'yxat o'zgargan.", show_alert=True)
        
    uni_name = universities[idx]
    
    if uni_name in selected:
        selected.remove(uni_name)
    else:
        selected.append(uni_name)
        
    await state.update_data(gift_all_selected_unis=selected)
    
    kb = build_multiselect_kb(
        items=universities, 
        selected=selected, 
        prefix="gift_uni_", 
        next_action="gift_step_faculties"
    )
    
    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass # Message is not modified (same state)
    
    await call.answer()


# -------------------------------------------------------------
# 4.2 GIFT TO ALL START - SELECT FACULTIES (STEP 2)
# -------------------------------------------------------------
@router.callback_query(OwnerGifts.selecting_universities_all, F.data == "gift_step_faculties")
async def cb_step_faculties(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected_unis = data.get("gift_all_selected_unis", [])
    
    stmt = select(Student.faculty_name).where(Student.faculty_name.isnot(None))
    if selected_unis:
        stmt = stmt.where(Student.university_name.in_(selected_unis))
        
    stmt = stmt.distinct().order_by(Student.faculty_name)
    rows = await session.execute(stmt)
    faculties = [r[0] for r in rows.all()]
    
    if not faculties:
        # Skip this step if no faculties found for the combination
        await state.update_data(gift_all_faculties=[], gift_all_selected_faculties=[])
        return await cb_step_specialties(call, state, session, skip=True)
        
    await state.update_data(gift_all_faculties=faculties, gift_all_selected_faculties=[])
    await state.set_state(OwnerGifts.selecting_faculties_all)
    
    kb = build_multiselect_kb(
        items=faculties, 
        selected=[], 
        prefix="gift_fac_", 
        next_action="gift_step_specialties"
    )
    
    uni_text = "Barchasi" if not selected_unis else f"{len(selected_unis)} ta tanlandi"
    
    await call.message.edit_text(
        f"📢 <b>Barchaga Premium berish - Filtr (2/4)</b>\n\n"
        f"🏫 Universitet: {uni_text}\n\n"
        "Qaysi Fakultet(lar) uchun premium bermoqchisiz?\n"
        "<i>Barchasini tanlash uchun shunchaki \"Keyingisi\" tugmasini bosing.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(OwnerGifts.selecting_faculties_all, F.data.startswith("gift_fac_"))
async def cb_toggle_faculty(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    idx = int(call.data.split("_")[2])
    data = await state.get_data()
    
    faculties = data.get("gift_all_faculties", [])
    selected = data.get("gift_all_selected_faculties", [])
    
    if idx >= len(faculties):
        return await call.answer("Xatolik: Ro'yxat o'zgargan.", show_alert=True)
        
    fac_name = faculties[idx]
    
    if fac_name in selected:
        selected.remove(fac_name)
    else:
        selected.append(fac_name)
        
    await state.update_data(gift_all_selected_faculties=selected)
    
    kb = build_multiselect_kb(
        items=faculties, 
        selected=selected, 
        prefix="gift_fac_", 
        next_action="gift_step_specialties"
    )
    try: await call.message.edit_reply_markup(reply_markup=kb)
    except Exception: pass
    await call.answer()


# -------------------------------------------------------------
# 4.3 GIFT TO ALL START - SELECT SPECIALTIES (STEP 3)
# -------------------------------------------------------------
@router.callback_query(OwnerGifts.selecting_faculties_all, F.data == "gift_step_specialties")
async def cb_step_specialties(call: CallbackQuery, state: FSMContext, session: AsyncSession, skip=False):
    data = await state.get_data()
    selected_unis = data.get("gift_all_selected_unis", [])
    selected_facs = data.get("gift_all_selected_faculties", [])
    
    stmt = select(Student.specialty_name).where(Student.specialty_name.isnot(None))
    if selected_unis:
        stmt = stmt.where(Student.university_name.in_(selected_unis))
    if selected_facs:
        stmt = stmt.where(Student.faculty_name.in_(selected_facs))
        
    stmt = stmt.distinct().order_by(Student.specialty_name)
    rows = await session.execute(stmt)
    specialties = [r[0] for r in rows.all()]
    
    if not specialties:
        await state.update_data(gift_all_specialties=[], gift_all_selected_specialties=[])
        return await cb_step_duration(call, state, session, skip=True)
        
    await state.update_data(gift_all_specialties=specialties, gift_all_selected_specialties=[])
    await state.set_state(OwnerGifts.selecting_specialties_all)
    
    kb = build_multiselect_kb(
        items=specialties, 
        selected=[], 
        prefix="gift_spec_", 
        next_action="gift_step_duration"
    )
    
    fac_text = "Barchasi" if not selected_facs else f"{len(selected_facs)} ta tanlandi"
    
    await call.message.edit_text(
        f"📢 <b>Barchaga Premium berish - Filtr (3/4)</b>\n\n"
        f"🏛 Fakultet: {fac_text}\n\n"
        "Qaysi Yo'nalish(lar) uchun premium bermoqchisiz?\n"
        "<i>Barchasini tanlash uchun shunchaki \"Keyingisi\" tugmasini bosing.</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    if not skip: await call.answer()

@router.callback_query(OwnerGifts.selecting_specialties_all, F.data.startswith("gift_spec_"))
async def cb_toggle_specialty(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    idx = int(call.data.split("_")[2])
    data = await state.get_data()
    
    specialties = data.get("gift_all_specialties", [])
    selected = data.get("gift_all_selected_specialties", [])
    
    if idx >= len(specialties):
        return await call.answer("Xatolik: Ro'yxat o'zgargan.", show_alert=True)
        
    spec_name = specialties[idx]
    
    if spec_name in selected:
        selected.remove(spec_name)
    else:
        selected.append(spec_name)
        
    await state.update_data(gift_all_selected_specialties=selected)
    
    kb = build_multiselect_kb(
        items=specialties, 
        selected=selected, 
        prefix="gift_spec_", 
        next_action="gift_step_duration"
    )
    try: await call.message.edit_reply_markup(reply_markup=kb)
    except Exception: pass
    await call.answer()


# -------------------------------------------------------------
# 4.4 GIFT TO ALL START - SELECT DURATION (STEP 4)
# -------------------------------------------------------------
@router.callback_query(OwnerGifts.selecting_specialties_all, F.data == "gift_step_duration")
async def cb_step_duration(call: CallbackQuery, state: FSMContext, session: AsyncSession, skip=False):
    await state.set_state(OwnerGifts.selecting_duration_all)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 3 kun", callback_data="gift_all_dur_3d")],
        [InlineKeyboardButton(text="📅 Bir hafta", callback_data="gift_all_dur_7d")],
        [InlineKeyboardButton(text="📅 10 kun", callback_data="gift_all_dur_10d")],
        [InlineKeyboardButton(text="📅 Bir oy", callback_data="gift_all_dur_1m"), InlineKeyboardButton(text="📅 Uch oy", callback_data="gift_all_dur_3m")],
        [InlineKeyboardButton(text="📅 Olti oy", callback_data="gift_all_dur_6m"), InlineKeyboardButton(text="📅 Bir yil", callback_data="gift_all_dur_1y")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="owner_gifts_menu")]
    ])
    
    data = await state.get_data()
    selected_unis = data.get("gift_all_selected_unis", [])
    selected_facs = data.get("gift_all_selected_faculties", [])
    selected_specs = data.get("gift_all_selected_specialties", [])
    
    filter_summary = []
    if selected_unis: filter_summary.append(f"🏫 <b>Universitetlar:</b> {len(selected_unis)} ta")
    if selected_facs: filter_summary.append(f"🏛 <b>Fakultetlar:</b> {len(selected_facs)} ta")
    if selected_specs: filter_summary.append(f"🎓 <b>Yo'nalishlar:</b> {len(selected_specs)} ta")
    
    summary_text = "\n".join(filter_summary) if filter_summary else "🌐 Barcha foydalanuvchilar (Filtrlanmagan)"
    
    await call.message.edit_text(
        f"📢 <b>Barchaga Premium berish - Muddat (4/4)</b>\n\n"
        f"Sizning tanlovingiz:\n{summary_text}\n\n"
        "Yuqoridagi auditoriya uchun qancha muddatga Premium bermoqchisiz?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    if not skip: await call.answer()


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
    elif duration_code == "3m":
        expiry_date = now + timedelta(days=90)
        duration_text = "Uch oy"
    elif duration_code == "6m":
        expiry_date = now + timedelta(days=180)
        duration_text = "Olti oy"
    elif duration_code == "1y":
        expiry_date = now + timedelta(days=365)
        duration_text = "Bir yil"
        
    # Bulk Update
    from sqlalchemy import update as sa_update
    
    data = await state.get_data()
    selected_unis = data.get("gift_all_selected_unis", [])
    selected_facs = data.get("gift_all_selected_faculties", [])
    selected_specs = data.get("gift_all_selected_specialties", [])
    
    # 1. Update Students
    stmt_student = sa_update(Student).values(
        is_premium=True,
        premium_expiry=expiry_date
    )
    
    # Apply Filters to Student Table
    if selected_unis:
        stmt_student = stmt_student.where(Student.university_name.in_(selected_unis))
    if selected_facs:
        stmt_student = stmt_student.where(Student.faculty_name.in_(selected_facs))
    if selected_specs:
        stmt_student = stmt_student.where(Student.specialty_name.in_(selected_specs))
        
    await session.execute(stmt_student)
    
    # 2. Update Users Table (Requires joining/subqueries or just using the identical fields if replicated)
    # Since User model doesn't store university_name natively from HEMIS, but Student does,
    # we can update User rows matching the Student rows we just updated.
    from sqlalchemy import select as sa_select
    student_logins_stmt = sa_select(Student.hemis_login)
    if selected_unis:
        student_logins_stmt = student_logins_stmt.where(Student.university_name.in_(selected_unis))
    if selected_facs:
        student_logins_stmt = student_logins_stmt.where(Student.faculty_name.in_(selected_facs))
    if selected_specs:
        student_logins_stmt = student_logins_stmt.where(Student.specialty_name.in_(selected_specs))
        
    stmt_user = sa_update(User).where(User.hemis_login.in_(student_logins_stmt)).values(
        is_premium=True,
        premium_expiry=expiry_date
    )
    
    await session.execute(stmt_user)
    
    await session.commit()
    
    # 4. Trigger Global Broadcast in background
    try:
        from services.notification_service import NotificationService
        
        filter_summary = []
        if selected_unis: filter_summary.append(f"Qamrov: {len(selected_unis)} ta OTM")
        if selected_facs: filter_summary.append(f"{len(selected_facs)} ta Fakultet")
        if selected_specs: filter_summary.append(f"{len(selected_specs)} ta Yo'nalish")
        target_info = "\n" + ", ".join(filter_summary) if filter_summary else ""
        
        NotificationService.run_broadcast.delay(
            title="🎁 Maxsus Premium sovg'asi!",
            body=f"Ma'muriyat tomonidan jamoamizga {duration_text} muddatga Premium obuna taqdim etildi! 🎉{target_info}",
            data={"type": "premium_gift"}
        )
    except Exception as e:
        logger.error(f"Global broadcast failed: {e}")

    await call.message.edit_text(
        f"✅ <b>Filtrlangan Guxruhga Premium berildi!</b>\n⏳ Muddat: {duration_text}\n\n"
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

    try:
        tg_acc = None
        if student:
            tg_acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == student.id))
        elif staff:
            tg_acc = await session.scalar(select(TgAccount).where(TgAccount.staff_id == staff.id))
            
        if tg_acc:
            msg = f"💰 <b>Balans to'ldirildi!</b>\n\nSizning hisobingizga {amount} so'm qo'shildi.\nJoriy balans: {current_balance} so'm."
            await message.bot.send_message(tg_acc.telegram_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Could not notify user via TG: {e}")

    await message.answer(
        f"✅ <b>Balans yangilandi!</b>\n\n"
        f"👤 {name}\n"
        f"➕ Qo'shildi: {amount} so'm\n"
        f"💰 Yangi balans: {current_balance} so'm",
        reply_markup=get_back_inline_kb("owner_gifts_menu"),
        parse_mode="HTML"
    )
    await state.clear()

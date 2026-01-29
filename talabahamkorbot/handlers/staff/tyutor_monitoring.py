"""
Tyutor Monitoring for Rahbariyat and Dekanat
"""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload

from database.models import Staff, TgAccount, TyutorKPI, Faculty, TyutorWorkLog, TutorGroup
from models.states import StaffStudentLookupStates, TyutorMonitoringStates # Use this for search state re-use or create new

router = Router()
# ... (rest of imports)

# ... (rest of code)

# ============================================================
# TYUTOR SEARCH & DETAILED VIEW
# ============================================================

@router.callback_query(F.data == "tyutor_search_start")
async def start_tutor_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(TyutorMonitoringStates.waiting_search_query) 
    
    await call.message.answer(
        "🔎 <b>Tyutor qidirish</b>\n\n"
        "Tyutorning <b>JSHSHIR</b> (14 raqam) yoki <b>Ism-familiyasini</b> yozib yuboring.\n\n"
        "<i>Na'muna: 30101901234567 yoki Akmalov Sardor</i>",
        parse_mode="HTML"
    )
    await call.answer()



async def _get_staff_with_role(telegram_id: int, session: AsyncSession):
    """Staff ni olish va rolini tekshirish"""
    tg_acc = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == telegram_id)
    )
    if not tg_acc or not tg_acc.staff_id:
        return None
    return await session.get(Staff, tg_acc.staff_id)


# ============================================================
# RAHBARIYAT MONITORING
# ============================================================

@router.callback_query(F.data == "rahb_tyutor_monitoring")
async def rahb_monitoring_menu(call: CallbackQuery, session: AsyncSession):
    """Rahbariyat uchun monitoring menyusi"""
    staff = await _get_staff_with_role(call.from_user.id, session)
    if not staff or staff.role != "rahbariyat":
        await call.answer("❌ Huquqingiz yo'q", show_alert=True)
        return

    text = """
👥 <b>TYUTOR MONITORING TIZIMI</b>

Quyidagi bo'limlardan birini tanlang:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Tyutor qidirish/hisoboti", callback_data="tyutor_search_start")],
        [InlineKeyboardButton(text="🏆 Umumiy Reyting (Top 20)", callback_data="rahb_monitoring_top")],
        [InlineKeyboardButton(text="🏢 Fakultetlar bo'yicha", callback_data="rahb_monitoring_faculties")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_menu")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "rahb_monitoring_top")
async def rahb_monitoring_top(call: CallbackQuery, session: AsyncSession):
    """Umumiy reyting"""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    
    # KPI bo'yicha top tyutorlar
    result = await session.execute(
        select(TyutorKPI, Staff, Faculty)
        .join(Staff, TyutorKPI.tyutor_id == Staff.id)
        .outerjoin(Faculty, Staff.faculty_id == Faculty.id)
        .where(TyutorKPI.quarter == quarter, TyutorKPI.year == year)
        .order_by(desc(TyutorKPI.total_kpi))
        .limit(20)
    )
    rows = result.all()
    
    if not rows:
        await call.answer("❌ Hozircha KPI ma'lumotlari yo'q", show_alert=True)
        return
    
    text = f"🏆 <b>TOP TYUTORLAR REYTINGI</b>\n\n"
    
    for i, (kpi, staff, faculty) in enumerate(rows, 1):
        icon = "🟢" if kpi.total_kpi >= 80 else "🟡" if kpi.total_kpi >= 60 else "🔴"
        faculty_name = faculty.short_name if faculty else "Noma'lum"
        text += f"{i}. {icon} <b>{staff.full_name}</b> ({faculty_name})\n"
        text += f"   KPI: {kpi.total_kpi:.1f}% (Qamrov: {kpi.coverage_score:.1f})\n\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Tyutor qidirish/hisoboti", callback_data="tyutor_search_start")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_tyutor_monitoring")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "rahb_monitoring_faculties")
async def rahb_monitoring_faculties(call: CallbackQuery, session: AsyncSession):
    """Fakultetlar ro'yxati"""
    faculties = await session.scalars(select(Faculty).where(Faculty.is_active == True))
    
    keyboard = []
    for faculty in faculties:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🏢 {faculty.name}", 
                callback_data=f"rahb_monitoring_faculty:{faculty.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_tyutor_monitoring")])
    
    await call.message.edit_text(
        "🏢 <b>Fakultetni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("rahb_monitoring_faculty:"))
async def rahb_monitoring_faculty_detail(call: CallbackQuery, session: AsyncSession):
    """Fakultet bo'yicha tyutorlar"""
    faculty_id = int(call.data.split(":")[1])
    
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    
    result = await session.execute(
        select(Staff, TyutorKPI)
        .outerjoin(TyutorKPI, (TyutorKPI.tyutor_id == Staff.id) & 
                             (TyutorKPI.quarter == quarter) & 
                             (TyutorKPI.year == year))
        .where(Staff.faculty_id == faculty_id, Staff.role == "tyutor")
        .order_by(desc(TyutorKPI.total_kpi))
    )
    rows = result.all()
    
    faculty = await session.get(Faculty, faculty_id)
    text = f"🏢 <b>{faculty.name} TYUTORLARI</b>\n\n"
    
    for i, (staff, kpi) in enumerate(rows, 1):
        if kpi:
            icon = "🟢" if kpi.total_kpi >= 80 else "🟡" if kpi.total_kpi >= 60 else "🔴"
            score = f"{kpi.total_kpi:.1f}%"
            details = f"Qamrov: {kpi.coverage_score:.1f} | Risk: {kpi.risk_detection_score:.1f}"
        else:
            icon = "⚪️"
            score = "0.0% (Hisoblanmagan)"
            details = "Hali hisoblanmagan"
            
        text += f"{i}. {icon} <b>{staff.full_name}</b>\n"
        text += f"   KPI: {score}\n"
        text += f"   └ {details}\n\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Tyutor qidirish/hisoboti", callback_data="tyutor_search_start")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_monitoring_faculties")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ============================================================
# DEKANAT MONITORING
# ============================================================

@router.callback_query(F.data == "dek_tyutor_monitoring")
async def dek_monitoring_menu(call: CallbackQuery, session: AsyncSession):
    """Dekanat uchun monitoring"""
    staff = await _get_staff_with_role(call.from_user.id, session)
    if not staff or staff.role != "dekanat" or not staff.faculty_id:
        await call.answer("❌ Huquqingiz yo'q yoki fakultet biriktirilmagan", show_alert=True)
        return

    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    
    # O'z fakulteti tyutorlari
    result = await session.execute(
        select(Staff, TyutorKPI)
        .outerjoin(TyutorKPI, (TyutorKPI.tyutor_id == Staff.id) & 
                             (TyutorKPI.quarter == quarter) & 
                             (TyutorKPI.year == year))
        .where(Staff.faculty_id == staff.faculty_id, Staff.role == "tyutor")
        .order_by(desc(TyutorKPI.total_kpi))
    )
    rows = result.all()
    
    text = f"🛡 <b>FAKULTET TYUTORLARI MONITORINGI</b>\n\n"
    
    for i, (tutor, kpi) in enumerate(rows, 1):
        if kpi:
            icon = "🟢" if kpi.total_kpi >= 80 else "🟡" if kpi.total_kpi >= 60 else "🔴"
            score = f"{kpi.total_kpi:.1f}%"
            details = f"Qamrov: {kpi.coverage_score:.1f} | Risk: {kpi.risk_detection_score:.1f}"
        else:
            icon = "⚪️"
            score = "0.0%"
            details = "Hali hisoblanmagan"
            
        text += f"{i}. {icon} <b>{tutor.full_name}</b>\n"
        text += f"   KPI: {score}\n"
        text += f"   └ {details}\n\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Tyutor qidirish/hisoboti", callback_data="tyutor_search_start")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="dek_menu")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ============================================================
# TYUTOR SEARCH & DETAILED VIEW
# ============================================================

@router.callback_query(F.data == "tyutor_search_start")
async def start_tutor_search(call: CallbackQuery, state: FSMContext):
    await state.set_state(StaffStudentLookupStates.waiting_input) # We reuse this state name or create new one in context
    # Assuming StaffStudentLookupStates has waiting_input
    
    # But wait, we should differentiate between Student Lookup and Tutor Lookup. 
    # Let's use a specific state indicator in data
    await state.update_data(search_mode="tutor")
    
    await call.message.answer(
        "🔎 <b>Tyutor qidirish</b>\n\n"
        "Tyutorning <b>JSHSHIR</b> (14 raqam) yoki <b>Ism-familiyasini</b> yozib yuboring.\n\n"
        "<i>Na'muna: 30101901234567 yoki Akmalov Sardor</i>",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(TyutorMonitoringStates.waiting_search_query)
async def process_tutor_search(message: Message, session: AsyncSession, state: FSMContext):
    print(f"DEBUG: process_tutor_search HIT. MsgType: {message.content_type}")
    
    if not message.text:
         await message.answer("⚠️ Iltimos, faqat ism yoki JSHSHIR raqamini yozing.")
         return

    # Identify who is searching
    searcher = await _get_staff_with_role(message.from_user.id, session)
    if not searcher:
        await message.answer("❌ Xatolik: Foydalanuvchi aniqlanmadi.")
        return

    query = message.text.strip()
    
    stmt = select(Staff).where(Staff.role == "tyutor")
    
    # SCOPING: If Dekanat, restrict to own faculty
    role_str = searcher.role.value if hasattr(searcher.role, "value") else str(searcher.role)
    
    if role_str == "dekanat":
        if not searcher.faculty_id:
            await message.answer("❌ Sizga fakultet biriktirilmagan.")
            return
        stmt = stmt.where(Staff.faculty_id == searcher.faculty_id)
    
    # Search Logic
    if query.isdigit() and len(query) == 14:
        # EXACT SEARCH by JSHSHIR
        stmt = stmt.where(Staff.jshshir == query)
    else:
        # FUZZY SEARCH by Name
        stmt = stmt.where(Staff.full_name.ilike(f"%{query}%"))

    staffs = (await session.scalars(stmt)).all()
    
    if not staffs:
        await message.answer(
            f"❌ <b>'{query}'</b> bo'yicha tyutor topilmadi.\n"
            "Qayta urinib ko'ring:",
            parse_mode="HTML"
        )
        return
        
    if len(staffs) > 1:
        text = "🔎 <b>Topilgan tyutorlar:</b>\n\n"
        kb = []
        for s in staffs[:10]:
             text += f"👤 {s.full_name} ({s.jshshir})\n"
             kb.append([InlineKeyboardButton(text=s.full_name, callback_data=f"view_tutor:{s.id}")])
             
        await message.answer(
            text + "\nIltimos, kerakli tyutorni tanlang:", 
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
    else:
        # Single result
        await show_tutor_details(message, staffs[0], session)
        await state.clear()


@router.callback_query(F.data.startswith("view_tutor:"))
async def view_tutor_callback(call: CallbackQuery, session: AsyncSession):
    tyutor_id = int(call.data.split(":")[1])
    tyutor = await session.get(Staff, tyutor_id)
    if tyutor:
        await show_tutor_details(call.message, tyutor, session)
        await call.message.delete()
    else:
        await call.answer("Tyutor topilmadi")


async def show_tutor_details(message: Message, tyutor: Staff, session: AsyncSession):
    # KPI Fetch
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    
    kpi = await session.scalar(
        select(TyutorKPI).where(TyutorKPI.tyutor_id == tyutor.id, TyutorKPI.quarter == quarter, TyutorKPI.year == year)
    )
    
    groups = await session.scalars(select(TutorGroup).where(TutorGroup.tutor_id == tyutor.id))
    group_list = ", ".join([g.group_number for g in groups])
    
    faculty = await session.get(Faculty, tyutor.faculty_id)
    faculty_name = faculty.name if faculty else "Noma'lum"

    score = f"{kpi.total_kpi:.1f}%" if kpi else "0.0%"
    
    text = (
        f"👤 <b>TYUTOR PROFILI</b>\n"
        f"Ism: <b>{tyutor.full_name}</b>\n"
        f"Fakultet: <b>{faculty_name}</b>\n"
        f"Guruhlar: {group_list}\n"
        f"JSHSHIR: {tyutor.jshshir}\n"
        f"Tel: {tyutor.phone}\n\n"
        f"📊 <b>KPI: {score}</b>\n\n"
    )

    # Calculate Log Stats
    log_stats = await session.execute(
        select(TyutorWorkLog.direction_type, func.count(TyutorWorkLog.id))
        .where(TyutorWorkLog.tyutor_id == tyutor.id)
        .group_by(TyutorWorkLog.direction_type)
    )
    stats_map = {row[0]: row[1] for row in log_stats.all()}
    
    cat_friendly = {
        "normativ": "Me'yoriy Hujjatlar",
        "darsdan_tashqari": "Darsdan tashqari",
        "manaviy": "Ma'naviy-ma'rifiy",
        "profilaktika": "Profilaktika",
        "turar_joy": "Turar joy",
        "ota_ona": "Ota-onalar bilan"
    }

    if stats_map:
        text += "<b>📋 Hisobotlar statistikasi:</b>\n"
        for key, name in cat_friendly.items():
            count = stats_map.get(key, 0)
            if count > 0:
                text += f"▫️ {name}: <b>{count} ta</b>\n"
        text += "\n"
    
    # Buttons for Work Directions
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Me'yoriy Hujjatlar", callback_data=f"tutor_log:normativ:{tyutor.id}")],
        [InlineKeyboardButton(text="🎭 Darsdan tashqari", callback_data=f"tutor_log:darsdan_tashqari:{tyutor.id}")],
        [InlineKeyboardButton(text="🕌 Ma'naviy-ma'rifiy", callback_data=f"tutor_log:manaviy:{tyutor.id}")],
        [InlineKeyboardButton(text="🛡 Jinoyatchilik profilaktikasi", callback_data=f"tutor_log:profilaktika:{tyutor.id}")],
        [InlineKeyboardButton(text="🏠 Turar joy (Ijara/TTJ)", callback_data=f"tutor_log:turar_joy:{tyutor.id}")],
        [InlineKeyboardButton(text="👨‍👩‍👧 Ota-onalar bilan ishlash", callback_data=f"tutor_log:ota_ona:{tyutor.id}")],
        [InlineKeyboardButton(text="⬅️ Yopish", callback_data="delete_msg")]
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("tutor_log:"))
async def view_tutor_log_category(call: CallbackQuery, session: AsyncSession):
    # data: tutor_log:CATEGORY:ID
    parts = call.data.split(":")
    category = parts[1]
    tyutor_id = int(parts[2])
    
    logs = await session.scalars(
        select(TyutorWorkLog)
        .where(TyutorWorkLog.tyutor_id == tyutor_id, TyutorWorkLog.direction_type == category)
        .order_by(desc(TyutorWorkLog.created_at))
        .limit(10)
    )
    
    logs_list = list(logs.all())
    
    cat_names = {
        "normativ": "Me'yoriy Hujjatlar",
        "darsdan_tashqari": "Darsdan tashqari faoliyat",
        "manaviy": "Ma'naviy-ma'rifiy ishlar",
        "profilaktika": "Jinoyatchilik va huquqbuzarlik profilaktikasi",
        "turar_joy": "Turar joy (Ijara/TTJ) bilan ishlash",
        "ota_ona": "Ota-onalar bilan ishlash"
    }
    
    title = cat_names.get(category, category)
    
    if not logs_list:
        await call.answer(f"{title} bo'yicha hisobotlar yo'q", show_alert=True)
        return
        
    await call.message.delete()
    
    header = f"📂 <b>{title.upper()}</b>\nHisobotlar ro'yxati:\n\n"
    await call.message.answer(header, parse_mode="HTML")
    
    for log in logs_list:
        content = (
            f"📅 <b>{log.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
            f"📝 {log.description}\n"
        )
        
        if log.file_id:
            # Send file/photo
            if log.file_type == "photo":
                await call.message.answer_photo(log.file_id, caption=content[:1024], parse_mode="HTML")
            elif log.file_type == "video":
                await call.message.answer_video(log.file_id, caption=content[:1024], parse_mode="HTML")
            elif log.file_type == "document":
                await call.message.answer_document(log.file_id, caption=content[:1024], parse_mode="HTML")
        else:
            await call.message.answer(content, parse_mode="HTML")
            
    # Back button
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga (Profil)", callback_data=f"view_tutor:{tyutor_id}")]
    ])
    await call.message.answer("---", reply_markup=kb)


@router.callback_query(F.data == "delete_msg")
async def delete_message_handler(call: CallbackQuery):
    await call.message.delete()

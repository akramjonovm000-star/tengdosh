"""
Tyutor Dashboard - KPI va statistika
"""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from aiogram.exceptions import TelegramBadRequest

from database.models import Staff, TgAccount, TutorGroup, Student, TyutorKPI
from services.kpi_calculator import calculate_tyutor_kpi
from keyboards.inline_kb import get_tutor_main_menu_kb

router = Router()


async def _get_tyutor_by_tg(telegram_id: int, session: AsyncSession):
    """Telegram ID orqali tyutorni topish"""
    tg_acc = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == telegram_id)
    )
    if not tg_acc or not tg_acc.staff_id:
        return None
    
    staff = await session.get(Staff, tg_acc.staff_id)
    if staff and staff.role == "tyutor":
        return staff
    return None


@router.callback_query(F.data == "tyutor_dashboard")
async def tyutor_dashboard(call: CallbackQuery, session: AsyncSession):
    """Tyutor asosiy dashboard"""
    print(f"DEBUG: tyutor_dashboard handler called by {call.from_user.id}")
    tyutor = await _get_tyutor_by_tg(call.from_user.id, session)
    
    if not tyutor:
        await call.answer("❌ Siz tyutor emassiz", show_alert=True)
        return
    
    # Joriy chorak va yil
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    year = now.year
    
    # KPI ni olish yoki hisoblash
    result = await session.execute(
        select(TyutorKPI).where(
            TyutorKPI.tyutor_id == tyutor.id,
            TyutorKPI.quarter == quarter,
            TyutorKPI.year == year
        )
    )
    kpi = result.scalar_one_or_none()
    
    if not kpi:
        # KPI hali hisoblanmagan, hisoblash
        total_kpi = await calculate_tyutor_kpi(tyutor.id, quarter, year, session)
        # Qayta olish
        result = await session.execute(
            select(TyutorKPI).where(
                TyutorKPI.tyutor_id == tyutor.id,
                TyutorKPI.quarter == quarter,
                TyutorKPI.year == year
            )
        )
        kpi = result.scalar_one_or_none()
    
    # Talabalar soni
    result = await session.execute(
        select(func.count(Student.id.distinct()))
        .join(TutorGroup, Student.group_number == TutorGroup.group_number)
        .where(TutorGroup.tutor_id == tyutor.id)
    )
    students_count = result.scalar() or 0
    
    # KPI emoji
    if kpi and kpi.total_kpi >= 80:
        kpi_emoji = "🟢"
    elif kpi and kpi.total_kpi >= 60:
        kpi_emoji = "🟡"
    else:
        kpi_emoji = "🔴"
    
    # Dashboard matni
    text = f"""
🧑‍🏫 <b>TYUTOR DASHBOARD</b>

👤 <b>Tyutor:</b> {tyutor.full_name}
📊 <b>Yil:</b> {year}

━━━━━━━━━━━━━━━━━━━━━━

📈 <b>UMUMIY KPI:</b> {kpi_emoji} <b>{kpi.total_kpi if kpi else 0:.1f}%</b>

<b>Tafsilotlar:</b>
├ 👥 Qamrov: {kpi.coverage_score if kpi else 0:.1f}/30
├ 🚨 Muammo aniqlash: {kpi.risk_detection_score if kpi else 0:.1f}/25
├ 🎯 Faollik: {kpi.activity_score if kpi else 0:.1f}/20
├ 👨‍👩‍👧 Ota-ona aloqasi: {kpi.parent_contact_score if kpi else 0:.1f}/15
└ ✅ Intizom: {kpi.discipline_score if kpi else 0:.1f}/10

━━━━━━━━━━━━━━━━━━━━━━

👥 <b>Talabalar:</b> {students_count} ta
📅 <b>Yangilangan:</b> {(kpi.updated_at + timedelta(hours=5)).strftime('%d.%m.%Y %H:%M') if kpi else 'Hali yangilanmagan'}
"""
    
    # Keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 KPI yangilash", callback_data=f"tyutor_refresh_kpi:{quarter}:{year}"),
        ],
        [
            InlineKeyboardButton(text="✅ 6 yo'nalish", callback_data="tyutor_work_directions"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="tutor_menu"),
        ]
    ])
    
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except TelegramBadRequest:
        await call.answer("✅ Ma'lumotlar yangilandi", show_alert=False)


@router.callback_query(F.data.startswith("tyutor_refresh_kpi:"))
async def tyutor_refresh_kpi(call: CallbackQuery, session: AsyncSession):
    """KPI ni qayta hisoblash"""
    tyutor = await _get_tyutor_by_tg(call.from_user.id, session)
    
    if not tyutor:
        await call.answer("❌ Xatolik", show_alert=True)
        return
    
    try:
        _, quarter_str, year_str = call.data.split(":")
        quarter = int(quarter_str)
        year = int(year_str)
    except:
        await call.answer("❌ Xatolik", show_alert=True)
        return
    
    await call.answer("⏳ KPI hisoblanmoqda...", show_alert=False)
    
    # KPI hisoblash
    total_kpi = await calculate_tyutor_kpi(tyutor.id, quarter, year, session)
    
    await call.answer(f"✅ KPI yangilandi: {total_kpi:.1f}%", show_alert=True)
    
    # Dashboard'ni qayta ko'rsatish
    await tyutor_dashboard(call, session)

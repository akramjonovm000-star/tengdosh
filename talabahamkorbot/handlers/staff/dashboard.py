from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import (
    Staff, Student, StudentFeedback, UserActivity, 
    TgAccount, StaffRole, TutorGroup, Faculty
)
from keyboards.inline_kb import (
    get_rahbariyat_main_menu_kb,
    get_dekanat_main_menu_kb,
    get_tutor_main_menu_kb,
    get_rahb_stat_menu_kb,
    get_faculties_stat_list_kb,
    get_faculty_stat_menu_kb,
    get_faculty_stat_menu_kb,
    get_groups_stat_list_kb,
    get_group_stat_menu_kb,
    get_dek_stat_menu_kb
)

router = Router()

async def get_activity_stats(session: AsyncSession, filters=None):
    """Faolliklar statistikasini hisoblash (Total, Approved, Rejected, Pending)"""
    stmt = select(UserActivity.status, func.count(UserActivity.id)).group_by(UserActivity.status)
    
    if filters:
        for cond in filters:
            stmt = stmt.where(cond)
            
    result = await session.execute(stmt)
    counts = {row[0]: row[1] for row in result.all()}
    
    return {
        "total": sum(counts.values()),
        "approved": counts.get("accepted", 0) + counts.get("approved", 0), # accepted va approved ni bir xil deb olamiz
        "rejected": counts.get("rejected", 0),
        "pending": counts.get("pending", 0)
    }

async def get_dashboard_text(session: AsyncSession, telegram_id: int) -> tuple[str, str, int | None]:
    """
    Returns (text, role, staff_id)
    """
    staff = await session.scalar(
        select(Staff)
        .join(TgAccount)
        .where(TgAccount.telegram_id == telegram_id)
    )
    if not staff:
        return "❌ Xodim hisobi topilmadi.", "unknown", None

    role = staff.role
    text = ""
    
    # ------------------------------------------------
    # RAHBARIYAT (Universitet darajasi)
    # ------------------------------------------------
    if role in [StaffRole.RAHBARIYAT.value, StaffRole.OWNER.value]:
        student_count = await session.scalar(select(func.count(Student.id))) or 0
        staff_count = await session.scalar(select(func.count(Staff.id))) or 0
        
        # Murojaatlar
        total_fb = await session.scalar(select(func.count(StudentFeedback.id))) or 0
        pending_fb = await session.scalar(select(func.count(StudentFeedback.id)).where(StudentFeedback.status == "pending")) or 0
        
        # Faolliklar
        act_stats = await get_activity_stats(session)

        text = (
            f"📊 <b>Universitet Statistikasi (Umumiy)</b>\n\n"
            f"👤 <b>Talabalar:</b> {student_count}\n"
            f"👨‍💼 <b>Xodimlar:</b> {staff_count}\n\n"
            f"📨 <b>Murojaatlar:</b>\n"
            f"• Jami: {total_fb}\n"
            f"• Kutilmoqda: {pending_fb}\n\n"
            f"📝 <b>Faolliklar:</b>\n"
            f"• Jami: {act_stats['total']}\n"
            f"• Tasdiqlangan: {act_stats['approved']}\n"
            f"• Rad etilgan: {act_stats['rejected']}\n"
            f"• Kutilmoqda: {act_stats['pending']}"
        )

    # ------------------------------------------------
    # DEKANAT (Fakultet darajasi)
    # ------------------------------------------------
    elif role == StaffRole.DEKANAT.value:
        if not staff.faculty_id:
             return "❌ Sizga fakultet biriktirilmagan.", role, staff.id
             
        faculty = await session.get(Faculty, staff.faculty_id)
        fac_name = faculty.name if faculty else "Noma'lum"

        student_count = await session.scalar(select(func.count(Student.id)).where(Student.faculty_id == staff.faculty_id)) or 0
        
        # Murojaatlar
        dek_fb_total = await session.scalar(
            select(func.count(StudentFeedback.id)).where(StudentFeedback.assigned_role == "dekanat", StudentFeedback.assigned_staff_id == staff.id)
        ) or 0
        dek_fb_pending = await session.scalar(
            select(func.count(StudentFeedback.id)).where(StudentFeedback.status == "assigned_dekanat", StudentFeedback.assigned_staff_id == staff.id)
        ) or 0
        
        # Faolliklar (shu fakultet studentlari)
        act_stats = await get_activity_stats(session, filters=[Student.faculty_id == staff.faculty_id]) # Join kerak bo'ladi queryda
        
        # To'g'rilash: get_activity_stats helper funksiyasi oddiy query qiladi. Joinni tashqarida qilish kerak yoki helperni o'zgartirish kerak.
        # Keling, oddiyroq qilib shu yerda yozamiz activity querysini.
        
        act_stmt = select(UserActivity.status, func.count(UserActivity.id)).join(Student).where(Student.faculty_id == staff.faculty_id).group_by(UserActivity.status)
        act_res = await session.execute(act_stmt)
        act_counts = {row[0]: row[1] for row in act_res.all()}
        
        act_approved = act_counts.get("accepted", 0) + act_counts.get("approved", 0)
        
        text = (
            f"📊 <b>Fakultet Statistikasi ({fac_name})</b>\n\n"
            f"👤 <b>Talabalar:</b> {student_count}\n\n"
            f"📨 <b>Murojaatlar (Sizga):</b>\n"
            f"• Jami: {dek_fb_total}\n"
            f"• Yangi: {dek_fb_pending}\n\n"
            f"📝 <b>Faolliklar:</b>\n"
            f"• Jami: {sum(act_counts.values())}\n"
            f"• Tasdiqlangan: {act_approved}\n"
            f"• Kutilmoqda: {act_counts.get('pending', 0)}"
        )

    # ------------------------------------------------
    # TYUTOR (Guruh darajasi)
    # ------------------------------------------------
    elif role == StaffRole.TYUTOR.value:
        groups = await session.scalars(select(TutorGroup).where(TutorGroup.tutor_id == staff.id))
        groups_list = groups.all()
        group_names = [g.group_number for g in groups_list]
        
        if not group_names:
            return "⚠️ Sizga guruh biriktirilmagan.", role, staff.id
            
        student_count = await session.scalar(select(func.count(Student.id)).where(Student.group_number.in_(group_names))) or 0
        
        # Faolliklar
        act_stmt = select(UserActivity.status, func.count(UserActivity.id)).join(Student).where(Student.group_number.in_(group_names)).group_by(UserActivity.status)
        act_res = await session.execute(act_stmt)
        act_counts = {row[0]: row[1] for row in act_res.all()}
        act_approved = act_counts.get("accepted", 0) + act_counts.get("approved", 0)

        text = (
            f"📊 <b>Tyutor Statistikasi</b>\n"
            f"👥 <b>Guruhlar:</b> {', '.join(group_names)}\n\n"
            f"👤 <b>Talabalar:</b> {student_count}\n\n"
            f"📝 <b>Faolliklar:</b>\n"
            f"• Jami: {sum(act_counts.values())}\n"
            f"• Tasdiqlangan: {act_approved}\n"
            f"• Kutilmoqda: {act_counts.get('pending', 0)}"
        )

    else:
        text = "⚠️ Statistika mavjud emas."
        
    return text, role, staff.id


@router.callback_query(F.data == "staff_stats")
async def show_staff_stats(call: CallbackQuery, session: AsyncSession):
    text, role, _ = await get_dashboard_text(session, call.from_user.id)
    
    kb = None
    if role in [StaffRole.RAHBARIYAT.value, StaffRole.OWNER.value]:
        # Rahbariyat uchun maxsus menyu (Fakultetlar kesimi tugmasi bilan)
        kb = get_rahb_stat_menu_kb()
    elif role == StaffRole.DEKANAT.value:
        staff_obj = await session.scalar(select(Staff).join(TgAccount).where(TgAccount.telegram_id == call.from_user.id))
        if staff_obj and staff_obj.faculty_id:
             kb = get_dek_stat_menu_kb(staff_obj.faculty_id)
        else:
             kb = get_dekanat_main_menu_kb()

    elif role == StaffRole.TYUTOR.value:
        kb = get_tutor_main_menu_kb()
        
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass
    await call.answer()


# ============================================================
# DRILL-DOWN HANDLERS (Rahbariyat)
# ============================================================

@router.callback_query(F.data == "stat_faculty_list")
async def show_faculty_list(call: CallbackQuery, session: AsyncSession):
    faculties = await session.scalars(select(Faculty).order_by(Faculty.name))
    kb = get_faculties_stat_list_kb(faculties.all())
    
    try:
        await call.message.edit_text("🏢 <b>Qaysi fakultet statistikasini ko'rmoqchisiz?</b>", reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("stat_faculty:"))
async def show_faculty_stats(call: CallbackQuery, session: AsyncSession):
    try:
        _, fac_id_str = call.data.split(":")
        if not fac_id_str: 
             return await show_faculty_list(call, session)
        faculty_id = int(fac_id_str)
    except ValueError:
        return await call.answer("Xatolik: ID topilmadi")

    faculty = await session.get(Faculty, faculty_id)
    if not faculty:
        return await call.answer("Fakultet topilmadi")

    # 1. Talabalar soni
    student_count = await session.scalar(select(func.count(Student.id)).where(Student.faculty_id == faculty_id)) or 0
    
    # 2. Faolliklar statistikasi
    act_stmt = select(UserActivity.status, func.count(UserActivity.id)).join(Student).where(Student.faculty_id == faculty_id).group_by(UserActivity.status)
    act_res = await session.execute(act_stmt)
    act_counts = {row[0]: row[1] for row in act_res.all()}
    act_approved = act_counts.get("accepted", 0) + act_counts.get("approved", 0)
    
    # 3. Murojaatlar statistikasi
    fb_stmt = select(StudentFeedback.status, func.count(StudentFeedback.id)).join(Student).where(Student.faculty_id == faculty_id).group_by(StudentFeedback.status)
    fb_res = await session.execute(fb_stmt)
    fb_counts = {row[0]: row[1] for row in fb_res.all()}
    
    fb_total = sum(fb_counts.values())
    fb_pending = fb_counts.get("pending", 0) + fb_counts.get("assigned_dekanat", 0) # Dekanatga biriktirilgan ham pending hisoblanadi
    fb_closed = fb_counts.get("closed", 0)

    text = (
        f"📊 <b>{faculty.name} Statistikasi</b>\n\n"
        f"👤 <b>Talabalar:</b> {student_count}\n\n"
        f"📨 <b>Murojaatlar:</b>\n"
        f"• Jami: {fb_total}\n"
        f"• Yopilgan: {fb_closed}\n"
        f"• Jarayonda: {fb_pending}\n\n"
        f"📝 <b>Faolliklar:</b>\n"
        f"• Jami: {sum(act_counts.values())}\n"
        f"• Tasdiqlangan: {act_approved}\n"
        f"• Rad etilgan: {act_counts.get('rejected', 0)}\n"
        f"• Kutilmoqda: {act_counts.get('pending', 0)}"
    )
    
    kb = get_faculty_stat_menu_kb(faculty_id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("stat_group_list:"))
async def show_group_list(call: CallbackQuery, session: AsyncSession):
    fac_id = int(call.data.split(":")[1])
    groups = await session.scalars(select(TutorGroup).where(TutorGroup.faculty_id == fac_id))
    
    kb = get_groups_stat_list_kb(groups.all(), fac_id)
    try:
        await call.message.edit_text("👥 <b>Qaysi guruhni ko'rmoqchisiz?</b>", reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("stat_group:"))
async def show_group_stats(call: CallbackQuery, session: AsyncSession):
    group_id = int(call.data.split(":")[1])
    group = await session.get(TutorGroup, group_id)
    
    if not group:
         return await call.answer("Guruh topilmadi")
         
    # 1. Talabalar
    student_count = await session.scalar(select(func.count(Student.id)).where(Student.group_number == group.group_number)) or 0
    
    # 2. Faolliklar
    act_stmt = select(UserActivity.status, func.count(UserActivity.id)).join(Student).where(Student.group_number == group.group_number).group_by(UserActivity.status)
    act_res = await session.execute(act_stmt)
    act_counts = {row[0]: row[1] for row in act_res.all()}
    act_approved = act_counts.get("accepted", 0) + act_counts.get("approved", 0)

    # 3. Murojaatlar
    fb_stmt = select(StudentFeedback.status, func.count(StudentFeedback.id)).join(Student).where(Student.group_number == group.group_number).group_by(StudentFeedback.status)
    fb_res = await session.execute(fb_stmt)
    fb_counts = {row[0]: row[1] for row in fb_res.all()}
    
    fb_total = sum(fb_counts.values())
    fb_pending = fb_counts.get("pending", 0) + fb_counts.get("assigned_dekanat", 0)
    fb_closed = fb_counts.get("closed", 0)

    text = (
        f"📊 <b>Guruh: {group.group_number}</b>\n\n"
        f"👤 <b>Talabalar:</b> {student_count}\n\n"
        f"📨 <b>Murojaatlar:</b>\n"
        f"• Jami: {fb_total}\n"
        f"• Yopilgan: {fb_closed}\n"
        f"• Jarayonda: {fb_pending}\n\n"
        f"📝 <b>Faolliklar:</b>\n"
        f"• Jami: {sum(act_counts.values())}\n"
        f"• Tasdiqlangan: {act_approved}\n"
        f"• Kutilmoqda: {act_counts.get('pending', 0)}"
    )
    
    kb = get_group_stat_menu_kb(group.faculty_id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await call.answer()

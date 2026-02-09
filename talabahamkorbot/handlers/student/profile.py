from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from services.hemis_service import HemisService
from services.university_service import UniversityService
from models.states import StudentProfileStates

from database.models import (
    Student,
    TgAccount,
    UserActivity,
    UserDocument,
    UserCertificate,
    StudentFeedback,
    Election,
    Staff,
    StaffRole
)
from keyboards.inline_kb import get_student_profile_menu_kb, get_student_main_menu_kb
from utils.student_utils import get_student_by_tg

router = Router()


async def _get_student_by_tg_local(telegram_id: int, session: AsyncSession):
    return await get_student_by_tg(telegram_id, session)

# ================================
# 🛠 Helper: Build Profile Caption
# ================================
async def get_student_profile_caption(student: Student, session: AsyncSession) -> str:
    # 📊 Faolliklar statistikasini yuklash
    total_activities = await session.scalar(select(func.count(UserActivity.id)).where(UserActivity.student_id == student.id)) or 0
    approved_activities = await session.scalar(select(func.count(UserActivity.id)).where(UserActivity.student_id == student.id, UserActivity.status == "approved")) or 0
    
    documents_count = await session.scalar(select(func.count(UserDocument.id)).where(UserDocument.student_id == student.id)) or 0
    certificates_count = await session.scalar(select(func.count(UserCertificate.id)).where(UserCertificate.student_id == student.id)) or 0
    
    total_feedbacks = await session.scalar(select(func.count(StudentFeedback.id)).where(StudentFeedback.student_id == student.id)) or 0
    answered_feedbacks = await session.scalar(select(func.count(StudentFeedback.id)).where(StudentFeedback.student_id == student.id, StudentFeedback.status == "answered")) or 0

    # Format text
    display_name = student.short_name or student.full_name
    
    group_display = student.group_number
    if group_display and len(group_display) > 5:
        group_display = group_display[:5].strip()

    uni = student.university_name or (student.university.name if student.university else '-')
    fac = student.faculty_name or (student.faculty.name if student.faculty else '-')
    
    level = student.level_name or "?" 
    sem = student.semester_name or "?"
    edu_form = student.education_form or "-"
    edu_type = student.education_type or "-"
    pay_form = student.payment_form or "-"
    status = student.student_status or "Aktiv"
    
    city = student.province_name or "-"
    dist = student.district_name or "-"
    phone = student.phone or "-"
    email = student.email or "-"
    accom = student.accommodation_name or "-"

    prem_status = "💡 Oddiy"
    if student.is_premium:
        prem_status = f"💎 PREMIUM"
        if student.premium_expiry:
             prem_status += f" (gacha: {student.premium_expiry.strftime('%d.%m.%Y')})"

    caption = (
        f"🎓 <b>{level} | {sem}</b>\n"
        f"👤 <b>{display_name}</b>\n"
        f"💳 Holat: <b>{prem_status}</b>\n\n"
        
        f"🏫 <b>O‘qish joyi:</b>\n"
        f"• OTM: {uni}\n"
        f"• Fakultet: {fac}\n"
        f"• Yo‘nalish: {student.specialty_name or 'Mutaxassislik'}\n"
        f"• Guruh: <b>{group_display}</b>\n\n"
        f"⏳ Qoldirilgan darslar: <b>{student.missed_hours} soat</b>\n\n"
        
        f"📚 <b>Ta’lim ma’lumotlari:</b>\n"
        f"• Status: {status}\n"
        f"• Shakli: {edu_form} | {edu_type}\n"
        f"• To‘lov: {pay_form}\n\n"
        
        f"📞 <b>Aloqa:</b>\n"
        f"• Tel: {phone}\n"
        f"• Email: {email}\n"
        f"• Manzil: {city}, {dist}\n\n"
        
        f"🏠 <b>Ijtimoiy holat:</b>\n"
        f"• Yashash joyi: {accom}\n\n"

        f"📊 <b>Platformadagi Faollik:</b>\n"
        f"• Faolliklar: {approved_activities}/{total_activities}\n"
        f"• Hujjatlar: {documents_count}\n"
        f"• Sertifikatlar: {certificates_count}\n"
        f"• Murojaatlar: {answered_feedbacks}/{total_feedbacks}"
    )
    return caption

# ================================
# 🛠 Helper: Send Profile View
# ================================
async def send_profile_view(target, student: Student, session: AsyncSession, is_edit: bool = False):
    """
    Sends or Edits the profile view.
    target: CallbackQuery or Message
    """
    caption = await get_student_profile_caption(student, session)
    
    # Check for active election
    has_active_election = False
    active_election = await session.scalar(
        select(Election).where(
            and_(
                Election.university_id == student.university_id,
                Election.status == "active"
            )
        ).order_by(Election.created_at.desc())
    )
    if active_election:
        if not active_election.deadline or active_election.deadline > datetime.utcnow():
            has_active_election = True

    # Developer check
    user_id = target.from_user.id
    result = await session.execute(
        select(Staff).where(
            Staff.telegram_id == user_id,
            Staff.role == StaffRole.DEVELOPER,
            Staff.is_active == True
        )
    )
    is_developer = result.scalar_one_or_none() is not None

    msg_target = target.message if isinstance(target, CallbackQuery) else target
    kb = get_student_profile_menu_kb(
        is_election_admin=student.is_election_admin, 
        has_active_election=has_active_election,
        is_developer=is_developer
    )
    
    try:
        if student.image_url:
            # Photo logic
            if is_edit and isinstance(target, CallbackQuery):
                 # Try to delete old and send new photo (Text->Photo replacement not supported by edit)
                 await msg_target.delete()
                 await msg_target.answer_photo(
                    photo=URLInputFile(student.image_url, filename="profile.jpg"),
                    caption=caption,
                    reply_markup=kb,
                    parse_mode="HTML"
                 )
            else:
                 # Just answer photo
                 await msg_target.answer_photo(
                    photo=URLInputFile(student.image_url, filename="profile.jpg"),
                    caption=caption,
                    reply_markup=kb,
                    parse_mode="HTML"
                 )
        else:
            # Text logic
            if is_edit and isinstance(target, CallbackQuery):
                 await msg_target.edit_text(caption, reply_markup=kb, parse_mode="HTML")
            else:
                 await msg_target.answer(caption, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        # Fallback
        try:
             await msg_target.answer(caption, reply_markup=kb, parse_mode="HTML")
        except: pass


@router.callback_query(F.data == "student_profile")
async def student_profile(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()

    student = await get_student_by_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Siz talaba sifatida ro‘yxatdan o‘tmagansiz!", show_alert=True)

    # 🔒 Auth Check & Update
    if student.hemis_token:
        base_url = UniversityService.get_api_url(student.hemis_login)
        status = await HemisService.check_auth_status(student.hemis_token, base_url=base_url)
        
        if status == "AUTH_ERROR":
            await state.set_state(StudentProfileStates.waiting_for_password)
            await call.message.edit_text(
                "⚠️ <b>Parolingiz o'zgargan!</b>\n\n"
                "Siz Hemis profilingiz parolini o'zgartirgansiz.\n"
                "Qoldirilgan darslarni hisoblash va ma'lumotlarni yangilash uchun, iltimos, <b>yangi parolni kiriting:</b>",
                parse_mode="HTML"
            )
            return await call.answer()
            
        if status == "OK":
             # Update missed hours
             try:
                 # Fetch ME to get current semester info
                 me_data = await HemisService.get_me(student.hemis_token, base_url=base_url)
                 current_sem_code = None
                 if me_data and "semester" in me_data:
                     try:
                         current_sem_code = str(me_data["semester"]["code"])
                     except: pass

                 abs_res = await HemisService.get_student_absence(student.hemis_token, semester_code=current_sem_code, student_id=student.id, base_url=base_url)
                 if abs_res and isinstance(abs_res, tuple):
                     student.missed_hours = abs_res[0]
                     await session.commit()
             except: pass

    # Show Profile
    await send_profile_view(call, student, session, is_edit=True)
    await call.answer()


@router.message(StudentProfileStates.waiting_for_password)
async def process_profile_password(message: Message, state: FSMContext, session: AsyncSession):
    password = message.text.strip()
    
    student = await get_student_by_tg(message.from_user.id, session)
    if not student:
        await state.clear()
        return await message.answer("Talaba ma'lumotlari topilmadi.")
        
    status_msg = await message.answer("⏳ Tekshirilmoqda...")
    
    # Try Auth
    base_url = UniversityService.get_api_url(student.hemis_login)
    token, error = await HemisService.authenticate(student.hemis_login, password, base_url=base_url)
    
    if token:
        # Success
        student.hemis_password = password
        student.hemis_token = token
        
        # Update Data immediately
        try:
             # Fetch ME to get current semester info
             me_data = await HemisService.get_me(token, base_url=base_url)
             current_sem_code = None
             if me_data and "semester" in me_data:
                 try:
                     current_sem_code = str(me_data["semester"]["code"])
                 except: pass
             
             abs_res = await HemisService.get_student_absence(token, semester_code=current_sem_code, student_id=student.id, base_url=base_url)
             if abs_res and isinstance(abs_res, tuple):
                 student.missed_hours = abs_res[0]
        except: pass
        
        await session.commit()
        await state.clear()
        
        await status_msg.delete() # Remove "Checking..."
        await message.answer("✅ <b>Parol yangilandi!</b>", parse_mode="HTML")
        
        # Show Profile automatically
        await send_profile_view(message, student, session, is_edit=False)
        
    else:
        await status_msg.edit_text(f"❌ <b>Parol noto'g'ri!</b> ({error or ''})\n\nIltimos, qaytadan urinib ko'ring:", parse_mode="HTML")

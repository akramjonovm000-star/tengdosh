import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Staff, StaffRole, Student, TgAccount, Club, User
from keyboards.inline_kb import get_retry_or_home_kb
from models.states import AuthStates
from services.hemis_service import HemisService
from services.university_service import UniversityService
from utils.text_utils import format_uzbek_name

router = Router()
logger = logging.getLogger(__name__)

# =====================================================================
#                     TALABA -> HEMIS LOGIN KIRITISH
# =====================================================================
@router.message(AuthStates.entering_hemis_login)
async def process_hemis(message: Message, state: FSMContext, session: AsyncSession):
    hemis = (message.text or "").strip()
    
    uni_name = UniversityService.get_university_name(hemis)
    api_url = UniversityService.get_api_url(hemis)
    
    greeting_header = "🔑 <b>HEMIS Parolini Kiriting</b>"
    if uni_name:
        greeting_header = f"🎓 <b>{uni_name}</b>\n\nAssalomu alaykum! Siz ushbu universitet talabasisiz."
        await state.update_data(hemis_login=hemis, base_url=api_url)
    else:
        await state.update_data(hemis_login=hemis)
        
    await state.set_state(AuthStates.entering_hemis_password)
    
    student = await session.scalar(select(Student).where(Student.hemis_login == hemis))
    
    if student:
        await message.answer(
            f"{greeting_header}\n\n"
            f"👤 <b>{student.full_name}</b>\n"
            "Haqiqatan ham siz ekanligingizni tasdiqlash uchun <b>HEMIS parolingizni</b> kiriting:",
            parse_mode="HTML",
             reply_markup=get_retry_or_home_kb()
        )
    else:
        await message.answer(
            f"{greeting_header}\n\n"
            "Tizimga kirish uchun parolingizni yozib yuboring:\n"
            "(Parol faqat sessiya olish uchun ishlatiladi)",
            reply_markup=get_retry_or_home_kb(),
            parse_mode="HTML"
        )


# =====================================================================
#                     TALABA -> HEMIS PAROL
# =====================================================================
@router.message(AuthStates.entering_hemis_password)
async def process_hemis_password(message: Message, state: FSMContext, session: AsyncSession):
    password = (message.text or "").strip()
    data = await state.get_data()
    login = data.get("hemis_login")
    base_url = data.get("base_url")

    token, error_msg = await HemisService.authenticate(login, password, base_url=base_url)

    if not token:
        msg_text = (
            f"❌ <b>Xatolik yuz berdi!</b>\n"
            f"Sababi: <i>{error_msg}</i>\n\n"
            "Iltimos, qaytadan urinib ko'ring."
        )
        return await message.answer(
            msg_text,
            reply_markup=get_retry_or_home_kb(),
            parse_mode="HTML"
        )

    # Fetch Profile
    me = await HemisService.get_me(token, base_url=base_url)
    if not me:
         return await message.answer("❌ HEMIS ma'lumotlarini yuklab bo'lmadi.")

    h_id = str(me.get("id", ""))
    
    first_name = me.get("first_name") or me.get("firstname") or me.get("firstName") or ""
    last_name = me.get("second_name") or me.get("lastname") or me.get("surname") or me.get("lastName") or ""
    patronymic = me.get("third_name") or me.get("fathername") or me.get("patronymic") or me.get("secondName") or ""
    full_name = me.get("full_name") or me.get("fullName") or f"{first_name} {last_name} {patronymic}".strip()
    
    # Process attributes
    uni_data = me.get("university")
    uni_name = uni_data.get("name") if isinstance(uni_data, dict) else uni_data if isinstance(uni_data, str) else None
    
    fac_name = None
    if isinstance(me.get("faculty"), dict): fac_name = me["faculty"].get("name")
    elif isinstance(me.get("department"), dict): fac_name = me["department"].get("name")
    
    # Format names
    first_name = format_uzbek_name(first_name)
    last_name = format_uzbek_name(last_name)
    patronymic = format_uzbek_name(patronymic)
    full_name = format_uzbek_name(full_name)
    short_name = format_uzbek_name(me.get("short_name", ""))
    
    image_url = me.get("image")
    level_name = me.get("level", {}).get("name") if isinstance(me.get("level"), dict) else None
    semester_name = me.get("semester", {}).get("name") if isinstance(me.get("semester"), dict) else None
    specialty_name = me.get("specialty", {}).get("name") if isinstance(me.get("specialty"), dict) else None
    
    # Determine Role
    user_type = me.get("type", "student")
    roles = me.get("roles", [])
    final_role_code = "student"
    
    if user_type == "employee" or me.get("employee_id_number"):
        final_role_code = "staff"
        for r in roles:
            r_obj = r if isinstance(r, dict) else {"name": str(r), "code": str(r)}
            code = str(r_obj.get("code", "")).lower()
            name = str(r_obj.get("name", "")).lower()
            if code == "tutor" or "tyutor" in name:
                final_role_code = "tutor"
                break
            elif code == "dean" or "dekan" in name:
                final_role_code = "dean"
                break
            elif code == "department" or "kafedra" in name:
                final_role_code = "department_head"
                break
            elif code == "head" or "rahbar" in name or "rektor" in name:
                final_role_code = "rahbariyat"
                break
                
    if user_type == "user":
        final_role_code = "student"

    # Sync to USERS table
    u = await session.scalar(select(User).where(User.hemis_login == login))
    if not u:
        u = User(
            hemis_login=login,
            role=final_role_code,
            full_name=full_name,
            short_name=short_name,
            image_url=image_url,
            hemis_id=h_id,
            hemis_token=token,
            hemis_password=password,
            university_name=uni_name,
            faculty_name=fac_name,
            specialty_name=specialty_name,
            group_number=me.get("group", {}).get("name") if isinstance(me.get("group"), dict) else None,
            level_name=level_name,
            semester_name=semester_name
        )
        session.add(u)
    else:
        u.role = final_role_code
        u.hemis_token = token
        u.hemis_password = password
        u.full_name = full_name
        u.short_name = short_name
        u.image_url = image_url
        if uni_name: u.university_name = uni_name
        if fac_name: u.faculty_name = fac_name

    await session.commit()
    
    # Sync to STUDENT or STAFF table
    if final_role_code == "student":
        student = await session.scalar(select(Student).where(Student.hemis_login == login))
        if not student:
            student = Student(
                hemis_login=login,
                hemis_password=password,
                hemis_token=token,
                full_name=full_name,
                short_name=short_name,
                pinfl=me.get("pinfl"),
                image_url=image_url,
                hemis_id=h_id
            )
            session.add(student)
            await session.commit()
            
        # Link TgAccount
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
        if not account:
            account = TgAccount(
                telegram_id=message.from_user.id,
                student_id=student.id,
                current_role="student"
            )
            session.add(account)
        else:
            account.student_id = student.id
            account.current_role = "student"
        
        await session.commit()
        await state.clear()
        
        await message.answer(
            f"🎉 <b>Tabriklaymiz, {short_name or full_name}!</b>\n\n"
            f"Siz tizimga muvaffaqiyatli kirdingiz. Bot orqali to'laqonli foydalanishingiz mumkin."
        )
    else:
        staff = await session.scalar(select(Staff).where(Staff.jshshir == me.get("pinfl", "xxx")))
        if not staff:
            staff = Staff(
                jshshir=me.get("pinfl", login),
                full_name=full_name,
                role=final_role_code,
                is_active=True
            )
            session.add(staff)
            await session.commit()
            
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
        if not account:
            account = TgAccount(
                telegram_id=message.from_user.id,
                staff_id=staff.id,
                current_role=final_role_code
            )
            session.add(account)
        else:
            account.staff_id = staff.id
            account.current_role = final_role_code
            
        await session.commit()
        await state.clear()
        
        await message.answer(
            f"🎉 <b>Xush kelibsiz, {full_name}!</b>\n\n"
            f"Xodim sifatida tizimga muvaffaqiyatli kirdingiz."
        )

# =====================================================================
#                     LOGOUT / EXIT
# =====================================================================
from aiogram.filters import Command
@router.message(Command("exit"))
async def cmd_exit(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    
    # Check link
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
    if account:
        await session.delete(account)
        await session.commit()
        await message.answer("✅ <b>Muvaffaqiyatli chiqildi.</b>\n\nQayta kirish uchun /start ni bosing.", parse_mode="HTML")
    else:
        await message.answer("Siz oldin tizimga kirmagansiz.", parse_mode="HTML")

# Catch-all for text to initiate login
from aiogram.filters import StateFilter
@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def handle_login_text_input(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip()
    # CHECK IF ALREADY AUTHENTICATED
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
    if account:
        return
        
    is_login_attempt = (text.isdigit() and len(text) >= 5) or (text.lower() in ["sanjar_botirovich", "tyutor_demo", "demo", "tyutor"])
    if not is_login_attempt:
        return
        
    await state.set_state(AuthStates.entering_hemis_login)
    await process_hemis(message, state, session)

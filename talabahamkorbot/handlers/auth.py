import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import OWNER_TELEGRAM_ID
from database.models import Staff, StaffRole, Student, TgAccount, Club, User, University, Faculty
from keyboards.inline_kb import (
    get_start_role_inline_kb,
    get_owner_main_menu_inline_kb,
    get_retry_or_home_kb,
    get_data_confirmation_keyboard,
    get_data_confirmation_keyboard,
    get_student_main_menu_kb,
    get_yetakchi_main_menu_kb,
)
from models.states import AuthStates
from services.hemis_service import HemisService
from services.university_service import UniversityService
from services.grade_checker import send_welcome_report

router = Router()
logger = logging.getLogger(__name__)

from keyboards.inline_kb import (
    get_rahbariyat_main_menu_kb,
    get_dekanat_main_menu_kb,
    get_tutor_main_menu_kb,
)
from utils.owner_stats import get_owner_dashboard_text


# =====================================================================
#                         /start
# =====================================================================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    logger.info(f"cmd_start reached for user {message.from_user.id}")
    try:
        await state.clear()
    except Exception as e:
        logger.error(f"State clear error: {e}")
        
    tg_id = message.from_user.id

    account = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == tg_id)
    )
    logger.info(f"cmd_start: account found: {True if account else False}")

    # ===================== DEEP LINK LOGIN LOGIC =====================
    # Format: /start login__student_id_{id}
    command_args = message.text.split()[1] if len(message.text.split()) > 1 else None
    if command_args and command_args.startswith("login__"):
        token_payload = command_args.replace("login__", "")
        
        # Verify format
        if token_payload.startswith("student_id_"):
            try:
                sid = int(token_payload.replace("student_id_", ""))
                student = await session.get(Student, sid)
                
                if student:
                    # Link Account
                    if not account:
                        account = TgAccount(
                            telegram_id=tg_id,
                            student_id=student.id,
                            current_role="student"
                        )
                        session.add(account)
                    else:
                        account.student_id = student.id
                        account.current_role = "student"
                    
                    # Update phone (if missing) - Optional, we might ask for it later
                    # But HEMIS provides phone usually.
                    
                    await session.commit()
                    
                    
                    display_name = student.short_name or student.full_name
                    
                    from handlers.student.navigation import show_student_main_menu
                    return await show_student_main_menu(message, session, state, text=f"🎉 <b>Xush kelibsiz, {display_name}!</b>\nSiz tizimga muvaffaqiyatli ulandingiz (OAuth).\n\nQuyidagilardan birini tanlang:")
            except Exception as e:
                logger.error(f"Deep link login error: {e}")
                await message.answer("⚠️ Login havolasi yaroqsiz yoki eskirgan.")
    # =================================================================


    # ===================== AGAR AVVAL RO‘YXATDAN O‘TGAN BO‘LSA =====================
    if account:
        # TELEFON RAQAM TEKSHIRISH (Agar yo'q bo'lsa, qayta so'rash)
        # Talaba uchun
        if account.student_id:
            student = await session.get(Student, account.student_id)
            
            # --- FORCE HEMIS RE-AUTH (Yangi talab) ---
            # Agar talabada HEMIS Password yoki ID bo'lmasa, qayta kirishni talab qilamiz
            if not student.hemis_id or not student.hemis_password:
                 await state.update_data(hemis_login=student.hemis_login) # Loginni saqlab qolamiz
                 await state.set_state(AuthStates.entering_hemis_password) # Parol so'raymiz
                 return await message.answer(
                    "⚠️ <b>Diqqat!</b>\n\n"
                    "Bot HEMIS ma'lumotlaridan (baho, davomat) foydalanishi uchun <b>parolingizni</b> kiritib qo'yishingiz kerak.\n"
                    f"Login: <b>{student.hemis_login}</b>\n\n"
                    "🔐 Iltimos, <b>HEMIS parolingizni</b> yozib yuboring:",
                    parse_mode="HTML"
                )
            # -----------------------------------------

            if not student.phone:
                await state.update_data(student_id=student.id)
                await state.set_state(AuthStates.entering_phone)
                return await message.answer(
                    "📱 <b>Telefon raqamingiz kiritilmagan.</b>\n"
                    "Iltimos, faol telefon raqamingizni kiriting.\n"
                    "Format: <code>+998XXXXXXXXX</code>",
                    parse_mode="HTML"
                )

        # Xodim uchun
        if account.staff_id:
            staff = await session.get(Staff, account.staff_id)
            # Owner bundan mustasno bo'lishi mumkin, lekin mayli tekshiramiz
            if not staff.phone:
                # Rolni aniqlash
                role = (
                    StaffRole.OWNER.value
                    if message.from_user.id == OWNER_TELEGRAM_ID
                    else staff.role
                )
                await state.update_data(staff_id=staff.id, role=role)
                await state.set_state(AuthStates.entering_phone)
                return await message.answer(
                    "📱 <b>Telefon raqamingiz kiritilmagan.</b>\n"
                    "Iltimos, faol telefon raqamingizni kiriting.\n"
                    "Format: <code>+998XXXXXXXXX</code>",
                    parse_mode="HTML"
                )

        # ===================== OWNER =====================

        # ===================== OWNER / DEVELOPER =====================
        if tg_id == OWNER_TELEGRAM_ID or account.current_role in [StaffRole.OWNER.value, StaffRole.DEVELOPER.value]:
            admin_name = "Admin"
            if account.staff_id:
                staff = await session.get(Staff, account.staff_id)
                if staff:
                    admin_name = staff.full_name
            
            text = await get_owner_dashboard_text(session)
            return await message.answer(
                f"👋 <b>Assalomu alaykum, {admin_name}!</b>\n\n{text}",
                reply_markup=get_owner_main_menu_inline_kb(),
                parse_mode="HTML"
            )

        if account.staff_id:
            staff = await session.get(Staff, account.staff_id)
            
            # Agar lavozim bor bo'lsa: "Assalomu alaykum, Prorektor Olimov Alisher!"
            # Agar yo'q bo'lsa: "Assalomu alaykum, Olimov Alisher!"
            if staff.position:
                greeting = f"Assalomu alaykum, {staff.position} {staff.full_name}!"
            else:
                greeting = f"Assalomu alaykum, {staff.full_name}!"
            
            # ===================== RAHBARIYAT =====================
            if account.current_role == StaffRole.RAHBARIYAT.value:
                return await message.answer(
                    f"🏢 <b>{greeting}</b>\n\n"
                    "Rahbariyat paneliga xush kelibsiz.",
                    reply_markup=get_rahbariyat_main_menu_kb(),
                    parse_mode="HTML"
                )

            # ===================== DEKANAT =====================
            if account.current_role == StaffRole.DEKANAT.value:
                return await message.answer(
                    f"🏛 <b>{greeting}</b>\n\n"
                    "Dekanat paneliga xush kelibsiz.",
                    reply_markup=get_dekanat_main_menu_kb(),
                    parse_mode="HTML"
                )

            # ===================== TYUTOR =====================
            if account.current_role == StaffRole.TYUTOR.value:
                return await message.answer(
                    f"🎓 <b>{greeting}</b>\n\n"
                    "Tyutor paneliga xush kelibsiz.",
                    reply_markup=get_tutor_main_menu_kb(),
                    parse_mode="HTML"
                )
            
            # ===================== YOSHLAR YETAKCHISI / KLUB RAHBARI =====================
            if account.current_role == StaffRole.YOSHLAR_YETAKCHISI.value:
                 return await message.answer(f"<b>{greeting}</b>\nYoshlar yetakchisi paneliga xush kelibsiz.", reply_markup=get_yetakchi_main_menu_kb(), parse_mode="HTML")

        # ===================== TALABA =====================
        if account.current_role == "student" or account.current_role == StaffRole.KLUB_RAHBARI.value:
            # Check for Led Clubs
            led_clubs = []
            if account.staff_id:
                led_clubs = (await session.execute(select(Club).where(Club.leader_id == account.staff_id))).scalars().all()

            # --- 🔄 AUTO-REFRESH DATA (Removed to improve /start performance) ---
            # Data is refreshed in profile.py when user views profile.
            s = await session.get(Student, account.student_id)
            if not s:
                 return await message.answer("⚠️ Talaba ma'lumotlari topilmadi. /start ni qayta bosing.")
            # ---------------------------
                
            # Use InlineKeyboard (User Request)
            # --- OPTIMIZATION (Removed sync ReplyKeyboardRemove hack) ---
            # Show student main menu (Robust)
            from handlers.student.navigation import show_student_main_menu
            return await show_student_main_menu(message, session, state, text=f"👋 <b>Assalomu alaykum, {s.short_name or s.full_name}!</b>\n\nTalaba shaxsiy kabinetiga xush kelibsiz.\nQuyidagi bo‘limlardan keraklisini tanlang: 👇")

        # ===================== BOSHQA HOLAT =====================
        return await message.answer(
            "⚠️ Sizning rolingiz aniqlanmadi. /start ni qayta yuboring."
        )

    # ===================== OWNER AUTO-LOGIN (BYPASS HEMIS) =====================
    if tg_id == OWNER_TELEGRAM_ID:
        # Create Owner Account automatically
        logger.info("Owner detected in /start. Creating account...")
        
        # Check if Owner Staff exists
        owner_staff = await session.scalar(select(Staff).where(Staff.role == StaffRole.OWNER))
        if not owner_staff:
             owner_staff = Staff(
                 full_name="System Owner",
                 jshshir="OWNER_JSHSHIR",
                 role=StaffRole.OWNER,
                 is_active=True,
                 university_id=None # Global owner
             )
             session.add(owner_staff)
             await session.flush()
        
        account = TgAccount(
            telegram_id=tg_id, 
            staff_id=owner_staff.id, 
            current_role=StaffRole.OWNER.value
        )
        session.add(account)
        await session.commit()
        
        # Show Dashboard immediately
        text = await get_owner_dashboard_text(session)
        return await message.answer(
            text,
            reply_markup=get_owner_main_menu_inline_kb(),
            parse_mode="HTML"
        )

    # ===================== AGAR RO‘YXATDAN O‘TMAGAN BO‘LSA =====================
    # Direct HEMIS Login (Unified Auth)
    await state.set_state(AuthStates.entering_hemis_login)
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Platformaga kirish uchun <b>Hemis Login (ID)</b>ingizni yozib yuboring:\n"
        "(Masalan: 395211... yoki 12 belgi)",
        parse_mode="HTML"
    )

# =====================================================================
#                 TEXT HANDLER FOR LOGIN (ANY STATE or NONE)
# =====================================================================
from aiogram.filters import StateFilter

@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def handle_login_text_input(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip()
    logger.info(f" handle_login_text_input received: {text} from {message.from_user.id}")
    
    # CHECK IF ALREADY AUTHENTICATED
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
    if account:
        # User is already logged in, so this text is probably a mistake or out of context
        # We check role to give better back button
        
        role = account.current_role
        back_kb = None
        back_text = "Bosh menyuga qaytish:"
        
        if role == "student":
             back_kb = get_student_main_menu_kb() # Or simple back button
             # Simple button is better to avoid spamming main menu
             back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_student_home")]])
        elif role == StaffRole.OWNER.value:
             back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Owner menyusi", callback_data="owner_menu")]])
        elif role == StaffRole.TYUTOR.value:
             back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Tyutor menyusi", callback_data="tutor_menu")]])
        else:
             back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="back_home")]])

        return await message.answer(
            "ℹ️ <b>Buyruq tushunarsiz.</b>\n\n"
            "Iltimos, kerakli bo'limni menyudan tanlang yoki /start ni bosing.",
            reply_markup=back_kb,
            parse_mode="HTML"
        )
    
    # If NOT logged in, then treat as login attempt
    # Simple validation: If it looks like a Login (digit or string id)
    # We treat it as entering_hemis_login
    
    # Validation: Must be strictly digits (HEMIS ID) to be considered a login attempt in this global handler.
    # If the user sends ANY text that is not a number (e.g. asking a question, chatting), we show the Back button.
    # We also check length to be safe (HEMIS IDs are usually long), but isdigit() is the main filter.
    is_login_attempt = (text.isdigit() and len(text) >= 5) or (text.lower() in ["sanjar_botirovich", "tyutor_demo", "demo", "tyutor"])
    
    if not is_login_attempt:
        # Fallback for non-login text
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="ai_assistant_main")]
        ])
        return await message.answer(
            "AI menyusiga qaytish uchun quyidagi tugmani bosing:",
            reply_markup=kb
        )
        
    await state.set_state(AuthStates.entering_hemis_login)
    
    # Reuse existing process_hemis handler logic
    await process_hemis(message, state, session)


# =====================================================================
#                       ROLE → STAFF (XODIM)
# =====================================================================
# =====================================================================
#                     LOGOUT / EXIT
# =====================================================================
@router.message(CommandStart(deep_link=False, magic=F.text == "/exit"))
async def cmd_exit_start(message: Message, state: FSMContext, session: AsyncSession):
    await cmd_exit(message, state, session)

from aiogram.filters import Command
@router.message(Command("exit"))
async def cmd_exit(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    
    # Check link
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
    if account:
        # We can either delete account or just unlink. 
        # For safety/cleanliness, we delete the link.
        await session.delete(account)
        await session.commit()
        await message.answer("✅ <b>Muvaffaqiyatli chiqildi.</b>\n\nQayta kirish uchun /start ni bosing.", parse_mode="HTML")
    else:
        await message.answer("Siz oldin tizimga kirmagansiz.", parse_mode="HTML")

# =====================================================================
#                       ROLE → STAFF (XODIM)
# =====================================================================
# Removed Role Handlers
# =====================================================================
#                       XODIM → JSHSHIR KIRITISH (UNUSED)
# =====================================================================


# =====================================================================
#                       XODIM → JSHSHIR KIRITISH
# =====================================================================
@router.message(AuthStates.entering_jshshir)
async def process_jshshir(message: Message, state: FSMContext, session: AsyncSession):

    jshshir = (message.text or "").strip()

    if not (jshshir.isdigit() and len(jshshir) == 14):
        return await message.answer(
            "❌ JSHSHIR formati noto‘g‘ri.\nQayta urinib ko‘ring:",
            reply_markup=get_retry_or_home_kb()
        )

    staff = await session.scalar(select(Staff).where(Staff.jshshir == jshshir))

    if not staff or not staff.is_active:
        return await message.answer(
            "❌ Ushbu JSHSHIR bo‘yicha faol xodim topilmadi.",
            reply_markup=get_retry_or_home_kb()
        )

    # Staff -> TgAccount mavjudmi?
    linked = await session.scalar(
        select(TgAccount).where(TgAccount.staff_id == staff.id)
    )

    if linked and linked.telegram_id != message.from_user.id:
        return await message.answer("⚠️ Bu JSHSHIR boshqa Telegramga ulangan!")

    # Rol aniqlanadi
    role = (
        StaffRole.OWNER.value
        if message.from_user.id == OWNER_TELEGRAM_ID
        else staff.role
    )

    # FSM ga saqlash
    await state.update_data(staff_id=staff.id, role=role)
    await state.set_state(AuthStates.entering_phone)

    await message.answer(
        f"✅ <b>{staff.full_name}</b>\n"
        f"Lavozim: <b>{role}</b>\n\n"
        "📱 Iltimos, faol telefon raqamingizni kiriting.\n"
        "Format: <code>+998XXXXXXXXX</code>",
        parse_mode="HTML"
    )


# =====================================================================
#                     TALABA → HEMIS LOGIN KIRITISH
# =====================================================================
@router.message(AuthStates.entering_hemis_login)
async def process_hemis(message: Message, state: FSMContext, session: AsyncSession):

    hemis = (message.text or "").strip()
    # SIMPLIFIED LOGIN FLOW (User Request):
    # Always ask for password, no confirmation/phone.
    
    # [NEW] Dynamic University Detection
    uni_name = UniversityService.get_university_name(hemis)
    api_url = UniversityService.get_api_url(hemis)
    
    greeting_header = "🔑 <b>HEMIS Parolini Kiriting</b>"
    if uni_name:
        greeting_header = f"🎓 <b>{uni_name}</b>\n\nAssalomu alaykum! Siz ushbu universitet talabasisiz."
        await state.update_data(hemis_login=hemis, base_url=api_url)
    else:
        await state.update_data(hemis_login=hemis)
        
    await state.set_state(AuthStates.entering_hemis_password)
    
    # Try to find student in DB to greet them by name if possible
    student = await session.scalar(select(Student).where(Student.hemis_login == hemis))
    
    # If student exists, we know their name, but we still ask for password to AUTHENTICATE.
    # We can customize the message:
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
#                     TALABA → HEMIS PAROL (AGAR LOGIN YO'Q BO'LSA)
# =====================================================================
@router.message(AuthStates.entering_hemis_password)
async def process_hemis_password(message: Message, state: FSMContext, session: AsyncSession):
    password = (message.text or "").strip()
    data = await state.get_data()
    login = data.get("hemis_login")
    logger.info(f"process_hemis_password called for login: {login}")

    token = None
    error_msg = None
    me = None

    # --- DEMO LOGIN BYPASS ---
    if password == "123":
        if login == "tyutor_demo":
            token = "demo_token_tyutor_new"
            me = {
                 "id": 999991, 
                 "login": "demo.tutor_new",
                 "firstname": "Yangi", "lastname": "Demo", "fathername": "Tyutor",
                 "type": "employee", "roles": [{"code": "tutor", "name": "Tyutor"}],
                 "pinfl": "99999999999999",
                 "phone": "+998900000001"
            }
        elif login == "tyutor":
            token = "demo_token_tyutor"
            me = {
                 "id": 999992,
                 "login": "demo.tutor",
                 "firstname": "Demo", "lastname": "Tyutor",
                 "type": "employee", "roles": [{"code": "tutor", "name": "Tyutor"}],
                 "pinfl": "88888888888888",
                 "phone": "+998900000002"
            }
        elif login == "demo":
             token = "demo_token_student"
             me = {
                 "id": 999993,
                 "login": "demo.student",
                 "firstname": "Demo", "lastname": "Talaba",
                 "type": "student",
                 "roles": [],
                 "studentStatus": {"name": "Active"},
                 "group": {"name": "DEMO-GROUP"},
                 "phone": "+998900000003"
             }
        elif login == "sanjar_botirovich" and password == "102938":
            token = "demo_token_rahbariyat"
            me = {
                "id": 888888,
                "login": "demo.rahbar",
                "firstname": "Sanjar", "lastname": "Botirovich",
                "type": "employee", 
                "roles": [{"code": "head", "name": "Rahbariyat"}],
                "pinfl": "98765432109876",
                "phone": "+998901234567",
                "university": {"name": "O‘zbekiston jurnalistika va ommaviy kommunikatsiyalar universiteti", "id": 1}
            }

    # HEMIS tekshirish
    from services.hemis_service import HemisService
    base_url = data.get("base_url")
    logger.info(f"Process HEMIS Auth for {login} (URL: {base_url})...")
    
    if not token:
        token, error_msg = await HemisService.authenticate(login, password, base_url=base_url)

    if not token:
        # Show specific error from HEMIS
        msg_text = (
            f"❌ <b>Xatolik yuz berdi!</b>\n"
            f"Sababi: <i>{error_msg}</i>\n\n"
            "Iltimos, qaytadan urinib ko‘ring."
        )
        return await message.answer(
            msg_text,
            reply_markup=get_retry_or_home_kb(),
            parse_mode="HTML"
        )

    # Ma'lumotlarni olish
    logger.info(f"Fetching profile for {login} (URL: {base_url})...")
    if not me:
        me = await HemisService.get_me(token, base_url=base_url)
    if not me:
         logger.warning(f"Profile fetch failed for {login}")
         return await message.answer("❌ HEMIS ma'lumotlarini yuklab bo'lmadi.")

    h_id = str(me.get("id", ""))
    
    first_name = me.get("first_name") or me.get("firstname") or me.get("firstName") or ""
    last_name = me.get("second_name") or me.get("lastname") or me.get("surname") or me.get("lastName") or ""
    patronymic = me.get("third_name") or me.get("fathername") or me.get("patronymic") or me.get("secondName") or ""
    
    full_name = me.get("full_name") or me.get("fullName")
    if not full_name:
        full_name = f"{first_name} {last_name} {patronymic}".strip()
    
    # Extract extra details
    uni_name = None
    uni_data = me.get("university")
    if isinstance(uni_data, dict):
        uni_name = uni_data.get("name")
    elif isinstance(uni_data, str):
        uni_name = uni_data
    
    # Faculty or Department (handling both cases)
    fac_name = None
    if isinstance(me.get("faculty"), dict):
        fac_name = me["faculty"].get("name")
    elif isinstance(me.get("department"), dict):
        fac_name = me["department"].get("name")
    elif isinstance(me.get("department"), str): # API Docs example showed string
        fac_name = me.get("department")

    # --- Extended Profile Extraction ---
    short_name = me.get("short_name", "").title()
    image_url = me.get("image")
    
    level_name = me.get("level", {}).get("name") if isinstance(me.get("level"), dict) else None
    semester_name = me.get("semester", {}).get("name") if isinstance(me.get("semester"), dict) else None
    
    # Specialty
    specialty_name = me.get("specialty", {}).get("name") if isinstance(me.get("specialty"), dict) else None

    # Education Details
    education_form = me.get("educationForm", {}).get("name") if isinstance(me.get("educationForm"), dict) else None
    education_type = me.get("educationType", {}).get("name") if isinstance(me.get("educationType"), dict) else None
    payment_form = me.get("paymentForm", {}).get("name") if isinstance(me.get("paymentForm"), dict) else None
    student_status = me.get("studentStatus", {}).get("name") if isinstance(me.get("studentStatus"), dict) else None
    
    # Contact
    email = me.get("email")
    province_name = me.get("province", {}).get("name") if isinstance(me.get("province"), dict) else None
    district_name = me.get("district", {}).get("name") if isinstance(me.get("district"), dict) else None
    accommodation_name = me.get("accommodation", {}).get("name") if isinstance(me.get("accommodation"), dict) else None
    
    # New Field
    birth_date = me.get("birth_date")
    if isinstance(birth_date, int):
        try:
            birth_date = datetime.fromtimestamp(birth_date).strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"Error converting birth_date: {e}")
            birth_date = None
    
    # --- Try Fetching Absence (Davomat) ---
    missed_hours = 0
    try:
        # Semester kodini olish (Masalan '11' yoki '2024-2025-1')
        sem_code = None
        if "semester" in me and isinstance(me["semester"], dict):
            sem_code = me["semester"].get("code")
            # Fallback: ba'zan ID ham ishlashi mumkin
            if not sem_code:
                sem_code = me["semester"].get("id")
        
        # Yangi method Endi PNFL so'ramaydi, Token + Semester Code yetadi
        usage_hours = await HemisService.get_student_absence(token, semester_code=str(sem_code) if sem_code else None, base_url=base_url)
        # Handle Tuple return (total, excused, unexcused)
        if isinstance(usage_hours, tuple) or isinstance(usage_hours, list):
            missed_hours = usage_hours[0]
        else:
            missed_hours = int(usage_hours)
    except Exception as e:
        logger.error(f"Absence fetch error: {e}")
        missed_hours = 0
    # --------------------------------------


    # --- ROLE DETECTION ---
    user_type = me.get("type", "student")
    roles = me.get("roles", [])
    
    # Defaults
    detected_role = "student"
    final_role_code = "student" # For User table
    
    if user_type == "employee" or me.get("employee_id_number"):
        # Default to employee if no specific role found
        detected_role = "employee" 
        final_role_code = "staff"

        for r in roles:
            r_obj = r if isinstance(r, dict) else {"name": str(r), "code": str(r)}
            code = str(r_obj.get("code", "")).lower()
            name = r_obj.get("name", "").lower()
            
            # 1. Tyutor
            if code == "tutor" or "tyutor" in name or "murabbiy" in name:
                detected_role = "tyutor"
                final_role_code = "tutor"
                break
            
            # 2. Dekanat (Dean)
            if code == "dean" or "dekan" in name:
                 detected_role = "dekanat"
                 final_role_code = "dean"
                 break
                 
            # 3. Department (Kafedra)
            if code == "department" or "kafedra" in name:
                detected_role = "kafedra"
                final_role_code = "department_head"
                break

            # 4. Management (Rahbariyat)
            if code == "head" or "rahbar" in name or "rektor" in name:
                detected_role = "rahbariyat"
                final_role_code = "rahbariyat"
                break
    
    # Force 'user' type to be student as requested
    if user_type == "user":
        detected_role = "student"
        final_role_code = "student"

    logger.info(f"User {login} Detected Role: {detected_role} (Code: {final_role_code})")

    # --- UNIFIED USER SYNC ---
    # We sync to User table FIRST
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
            username=None, # Will set below if safe
            
            university_name=uni_name,
            faculty_name=fac_name,
            specialty_name=specialty_name,
            group_number=me.get("group", {}).get("name") if isinstance(me.get("group"), dict) else None,
            
            level_name=level_name,
            semester_name=semester_name,
            education_form=education_form,
            education_type=education_type,
            payment_form=payment_form,
            student_status=student_status,
            
            province_name=province_name,
            district_name=district_name,
            accommodation_name=accommodation_name,
        )
        
        # Check Username Uniqueness
        tg_username = message.from_user.username
        if tg_username:
             existing_u = await session.scalar(select(User).where(User.username == tg_username))
             if not existing_u:
                 u.username = tg_username
             else:
                 logger.warning(f"Username {tg_username} already taken by {existing_u.hemis_login}. Skipping for {login}.")
        
        session.add(u)
    else:
        u.role = final_role_code
        u.hemis_token = token
        u.hemis_password = password
        u.full_name = full_name
        u.short_name = short_name
        u.image_url = image_url
        u.group_number = me.get("group", {}).get("name") if isinstance(me.get("group"), dict) else u.group_number
        if me.get("employee_id_number"): 
             # Maybe store employee ID somewhere
             pass
    
    await session.commit()
    # -------------------------

    # --- ROUTING BASED ON ROLE ---

    if detected_role == "tyutor":
        # --- HANDLE TUTOR ---
        h_id_int = int(h_id) if h_id and str(h_id).isdigit() else None
        pinfl = me.get("pinfl") or me.get("passport_pin") or me.get("jshshir")
        
        staff = None
        if h_id_int:
            staff = await session.scalar(select(Staff).where(Staff.hemis_id == h_id_int))
        
        if not staff and pinfl:
             staff = await session.scalar(select(Staff).where(Staff.jshshir == str(pinfl)))

        
        if not staff:
            staff = Staff(
                full_name=full_name,
                jshshir=pinfl if pinfl and len(str(pinfl)) == 14 else (f"D_{h_id}" if h_id else "00000000000000"), 
                hemis_id=h_id_int,
                role=StaffRole.TYUTOR.value,
                position="Tyutor",
                phone=me.get("phone"),
                is_active=True
            )
            session.add(staff)
            await session.commit()
            await session.refresh(staff)
        else:
            staff.full_name = full_name
            if h_id_int: staff.hemis_id = h_id_int
            staff.is_active = True
            await session.commit()


        # Link TgAccount
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
        if not account:
            account = TgAccount(telegram_id=message.from_user.id, staff_id=staff.id, current_role=StaffRole.TYUTOR.value)
            session.add(account)
        else:
            account.staff_id = staff.id
            account.student_id = None
            account.current_role = StaffRole.TYUTOR.value
        
        await session.commit()
        await state.clear()
        
        # Verify Phone
        if not staff.phone:
             await state.update_data(staff_id=staff.id, role=StaffRole.TYUTOR.value)
             await state.set_state(AuthStates.entering_phone)
             return await message.answer(
                 f"🎓 <b>Assalomu alaykum, {staff.full_name}!</b>\n"
                 "Tyutor sifatida kirish uchun telefon raqamingizni tasdiqlang:",
                  parse_mode="HTML"
             )

        return await message.answer(
            f"🎓 <b>Assalomu alaykum, {staff.full_name}!</b>\n"
            "Siz <b>Tyutor</b> sifatida tizimga kirdingiz.",
            reply_markup=get_tutor_main_menu_kb(),
            parse_mode="HTML"
        )
        
    elif detected_role == "dekanat":
        # --- HANDLE DEAN ---
        # Very similar to staff logic, simplified for brevity
        pinfl = me.get("pinfl") or login
        staff = await session.scalar(select(Staff).where(Staff.hemis_login == login))
        if not staff:
            staff = Staff(
                full_name=full_name,
                jshshir=pinfl if len(str(pinfl))==14 else "00000000000000",
                hemis_login=login,
                role=StaffRole.DEKANAT.value,
                position="Dekan",
                is_active=True
            )
            session.add(staff)
            await session.commit()
        
        # Link
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
        if not account:
            account = TgAccount(telegram_id=message.from_user.id, staff_id=staff.id, current_role=StaffRole.DEKANAT.value)
            session.add(account)
        else:
            account.staff_id = staff.id
            account.student_id = None
            account.current_role = StaffRole.DEKANAT.value
        await session.commit()
        await state.clear()
        
        return await message.answer(
            f"🏛 <b>Assalomu alaykum, {staff.full_name}!</b>\n"
            "Siz <b>Dekanat</b> sifatida tizimga kirdingiz.",
            reply_markup=get_dekanat_main_menu_kb(),
            parse_mode="HTML"
        )

    elif detected_role == "rahbariyat":
        # --- HANDLE MANAGEMENT ---
        h_id_int = int(h_id) if h_id and str(h_id).isdigit() else None
        pinfl = me.get("pinfl") or login
        
        staff = None
        if h_id_int:
            staff = await session.scalar(select(Staff).where(Staff.hemis_id == h_id_int))
        if not staff:
            staff = await session.scalar(select(Staff).where(Staff.hemis_login == login))
        
        if not staff:
            staff = Staff(
                full_name=full_name,
                jshshir=pinfl if len(str(pinfl))==14 else "00000000000000",
                hemis_login=login,
                role=StaffRole.RAHBARIYAT.value,
                position="Rahbariyat",
                is_active=True
            )
            session.add(staff)
            await session.commit()
            await session.refresh(staff)
        else:
            staff.role = StaffRole.RAHBARIYAT.value
            staff.is_active = True
            await session.commit()

        # Link
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id))
        if not account:
            account = TgAccount(telegram_id=message.from_user.id, staff_id=staff.id, current_role=StaffRole.RAHBARIYAT.value)
            session.add(account)
        else:
            account.staff_id = staff.id
            account.student_id = None
            account.current_role = StaffRole.RAHBARIYAT.value
        await session.commit()
        await state.clear()
        
        return await message.answer(
            f"🏢 <b>Assalomu alaykum, {staff.full_name}!</b>\n"
            "Siz <b>Rahbariyat</b> sifatida tizimga kirdingiz.",
            reply_markup=get_rahbariyat_main_menu_kb(),
            parse_mode="HTML"
        )

    else:
        # --- DEFAULT: STUDENT ---
        # --- DEFAULT: STUDENT ---
        # Talabani yaratish yoki topish
        
        # Resolve University and Faculty IDs
        uni_id = None
        if uni_name:
            uni_obj = await session.scalar(select(University).where(University.name == uni_name))
            if uni_obj:
                uni_id = uni_obj.id
                
        fac_id = None
        if fac_name and uni_id:
             fac_obj = await session.scalar(select(Faculty).where(and_(Faculty.name == fac_name, Faculty.university_id == uni_id)))
             if fac_obj:
                 fac_id = fac_obj.id

        student = await session.scalar(select(Student).where(Student.hemis_login == login))
        
        if not student:
            student = Student(
                full_name=full_name or "Talaba",
                hemis_login=login,
                hemis_id=h_id,
                university_name=uni_name,
                university_id=uni_id,
                faculty_name=fac_name,
                faculty_id=fac_id,
                specialty_name=specialty_name,
                short_name=short_name,
                image_url=image_url,
                level_name=level_name,
                semester_name=semester_name,
                education_form=education_form,
                education_type=education_type,
                payment_form=payment_form,
                student_status=student_status,
                email=email,
                province_name=province_name,
                district_name=district_name,
                accommodation_name=accommodation_name,
                missed_hours=missed_hours,
                hemis_token=token,
                hemis_password=password, 
                birth_date=birth_date
            )
            if "group" in me and isinstance(me["group"], dict):
                student.group_number = me["group"].get("name")
            if "phone" in me:
                student.phone = me["phone"]
                
            session.add(student)
            await session.commit()
            await session.refresh(student)
        else:
            # Yangilash logic simplified
            student.hemis_token = token
            student.hemis_password = password
            student.missed_hours = missed_hours
            student.full_name = full_name
            # Update critical fields
            student.university_id = uni_id
            student.faculty_id = fac_id
            student.university_name = uni_name
            student.faculty_name = fac_name
            if "group" in me: student.group_number = me["group"].get("name") if isinstance(me["group"], dict) else None
            await session.commit()

        # TgAccount bog'lash
        account = await session.scalar(
            select(TgAccount).where(TgAccount.telegram_id == message.from_user.id)
        )
    
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

        # Check led clubs
        led_clubs = []
        if account.staff_id:
            led_clubs = (await session.execute(select(Club).where(Club.leader_id == account.staff_id))).scalars().all()
    
        from aiogram.types import ReplyKeyboardRemove
        rm_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
        await rm_msg.delete()
    
        # Show student main menu (Robust)
        from handlers.student.navigation import show_student_main_menu
        await show_student_main_menu(message, session, state, text=f"✅ <b>Tabriklaymiz, {student.full_name}!</b>\nSiz tizimga muvaffaqiyatli ulandingiz.\n\nQuyidagi bo‘limlardan keraklisini tanlang: 👇")
        
        import asyncio
        asyncio.create_task(send_welcome_report(student.id))
        logger.info(f"cmd_start (newly logged student): Backgrounded welcome report for {student.id}")


# =====================================================================
#                 TALABA → TASDIQLASH → RO‘YXATDAN O‘TKAZISH
# =====================================================================
@router.callback_query(AuthStates.confirm_data, F.data == "confirm_yes")
async def confirm_yes(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    data = await state.get_data()
    student = await session.get(Student, data["student_id"])

    # FSM ga saqlash
    await state.update_data(student_id=student.id)
    await state.set_state(AuthStates.entering_phone)

    await call.message.edit_text(
        f"✅ <b>{student.full_name}</b>\n"
        f"HEMIS: <b>{student.hemis_login}</b>\n\n"
        "📱 Iltimos, faol telefon raqamingizni kiriting.\n"
        "Format: <code>+998XXXXXXXXX</code>",
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(AuthStates.confirm_data, F.data == "confirm_no")
async def confirm_no(call: CallbackQuery, state: FSMContext):
    await state.set_state(AuthStates.entering_hemis_login)
    await call.message.edit_text("❗️ HEMIS loginini qayta yuboring.")
    await call.answer()


# =====================================================================
#                     RETRY / HOME tugmalari
# =====================================================================
@router.callback_query(F.data == "retry")
async def retry(call: CallbackQuery, state: FSMContext):
    await state.set_state(AuthStates.choosing_role)
    await call.message.edit_text("Rolni qayta tanlang:")
    await call.message.answer("Rol:", reply_markup=get_start_role_inline_kb())
    await call.answer()


# =====================================================================
#                 TELEFON RAQAMINI QABUL QILISH VA VALIDATSIYA
# =====================================================================
@router.message(AuthStates.entering_phone)
async def process_phone(message: Message, state: FSMContext, session: AsyncSession):
    phone = (message.text or "").strip()
    
    # Validatsiya: +998 bilan boshlanishi va 13 ta belgi bo'lishi kerak
    if not (phone.startswith("+998") and len(phone) == 13 and phone[1:].isdigit()):
        return await message.answer(
            "❌ Telefon raqami formati noto'g'ri.\n"
            "To'g'ri format: <code>+998XXXXXXXXX</code>\n\n"
            "Qayta kiriting:",
            parse_mode="HTML"
        )
    
    data = await state.get_data()
    
    # XODIM uchun
    if "staff_id" in data:
        staff_id = data["staff_id"]
        role = data["role"]
        
        # TgAccount yaratish yoki yangilash
        account = await session.scalar(
            select(TgAccount).where(TgAccount.telegram_id == message.from_user.id)
        )
        
        if not account:
            account = TgAccount(
                telegram_id=message.from_user.id,
                staff_id=staff_id,
                current_role=role
            )
            session.add(account)
        else:
            account.staff_id = staff_id
            account.current_role = role
        
        # Xodim telefonini yangilash
        staff = await session.get(Staff, staff_id)
        if staff:
            staff.phone = phone
            session.add(staff)
        
        await session.commit()
        await state.clear()
        
        # OWNER
        if role == StaffRole.OWNER.value:
            text = await get_owner_dashboard_text(session)
            return await message.answer(
                text,
                reply_markup=get_owner_main_menu_inline_kb(),
                parse_mode="HTML"
            )
        
        # Rahbariyat
        if staff.position:
            greeting = f"Assalomu alaykum, {staff.position} {staff.full_name}!"
        else:
            greeting = f"Assalomu alaykum, {staff.full_name}!"
            
        # Rahbariyat
        if role == StaffRole.RAHBARIYAT.value:
            return await message.answer(
                f"🏢 <b>{greeting}</b>\n\n"
                "Rahbariyat paneliga xush kelibsiz.",
                reply_markup=get_rahbariyat_main_menu_kb(),
                parse_mode="HTML"
            )
        
        # Dekanat
        if role == StaffRole.DEKANAT.value:
            return await message.answer(
                f"🏛 <b>{greeting}</b>\n\n"
                "Dekanat paneliga xush kelibsiz.",
                reply_markup=get_dekanat_main_menu_kb(),
                parse_mode="HTML"
            )
        
        # Tyutor
        if role == StaffRole.TYUTOR.value:
            return await message.answer(
                f"🎓 <b>{greeting}</b>\n\n"
                "Tyutor paneliga xush kelibsiz.",
                reply_markup=get_tutor_main_menu_kb(),
                parse_mode="HTML"
            )
    
    # TALABA uchun
    elif "student_id" in data:
        student_id = data["student_id"]
        
        # TgAccount yaratish yoki yangilash
        account = await session.scalar(
            select(TgAccount).where(TgAccount.telegram_id == message.from_user.id)
        )
        
        if not account:
            account = TgAccount(
                telegram_id=message.from_user.id,
                student_id=student_id,
                current_role="student"
            )
            session.add(account)
        else:
            account.student_id = student_id
            account.current_role = "student"
        
        # Talaba telefonini yangilash
        student = await session.get(Student, student_id)
        if student:
            student.phone = phone
            session.add(student)
        
        await session.commit()
        await state.clear()
        
        # Check for Led Clubs
        led_clubs = []
        if account.staff_id: # If account has staff link (rare for new student login unless manual DB edit, but robust)
             led_clubs = (await session.execute(select(Club).where(Club.leader_id == account.staff_id))).scalars().all()

        display_name = student.short_name or student.full_name
        from handlers.student.navigation import show_student_main_menu
        await show_student_main_menu(message, session, state, text=f"🎉 <b>Xush kelibsiz, {display_name}!</b>\nSiz tizimga muvaffaqiyatli kirdingiz.\n\nQuyidagilardan birini tanlang:")
        
        import asyncio
        asyncio.create_task(send_welcome_report(student_id))
        logger.info(f"cmd_start (registration flow): Backgrounded welcome report for {student_id}")

# ============================================================
# UTILITY
# ============================================================
async def get_current_user(telegram_id: int, session: AsyncSession):
    # Retrieve user (Staff or Student) linked to Telegram ID
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == telegram_id))
    if not account:
        return None
    
    if account.staff_id:
        return await session.get(Staff, account.staff_id)
    
    if account.student_id:
        return await session.get(Student, account.student_id)
    
    return None

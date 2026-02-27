from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import Student, Staff, TgAccount
from models.states import TelegramBindState
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject, session: AsyncSession, state: FSMContext):
    """
    Handles Deep Links:
    1. Authorization Code (Legacy): auth_{uuid}
    2. OAuth/App Login: login__{token} (e.g., login__student_id_123 or login__staff_id_456)
    """
    args = command.args
    user_id = message.from_user.id
    
    if not args:
        return

    # --- 1. LEGACY AUTH FLOW ---
    if args.startswith("auth_"):
        from api.auth import verify_login # Import locally to avoid circulars
        auth_uuid = args.replace("auth_", "")
        success = verify_login(auth_uuid, user_id)
        
        if success:
            await message.answer("✅ <b>Tizimga muvaffaqiyatli kirdingiz!</b>\n\nIlovaga qaytishingiz mumkin.", parse_mode="HTML")
        else:
            await message.answer("❌ <b>Xatolik!</b>\nLogin sessiyasi eskirgan yoki noto'g'ri.", parse_mode="HTML")
        return

    # --- 2. OAUTH/APP LOGIN FLOW WITH PHONE VERIFICATION ---
    elif args.startswith("login__"): # Double underscore separator
        token = args.replace("login__", "")
        
        # Parse Token: student_id_123 or staff_id_456
        parts = token.split("_id_")
        if len(parts) != 2:
            await message.answer("❌ <b>Xatolik!</b>\nNoto'g'ri token formati.", parse_mode="HTML")
            return
            
        role_type, db_id = parts[0], parts[1] # role_type: student | staff
        
        if not db_id.isdigit():
            await message.answer("❌ <b>Xatolik!</b>\nID noto'g'ri formatda.", parse_mode="HTML")
            return
                
        db_id = int(db_id)
        
        # Check if user already bound
        result = await session.execute(select(TgAccount).where(TgAccount.telegram_id == user_id))
        tg_account = result.scalar_one_or_none()
        
        if role_type == "student":
            user_model = Student
        else:
            user_model = Staff
            
        # Verify db user exists
        user_result = await session.execute(select(user_model).where(user_model.id == db_id))
        db_user = user_result.scalar_one_or_none()
        
        if not db_user:
            await message.answer("❌ Tizimda profilingiz topilmadi.", parse_mode="HTML")
            return
            
        # If already bound to this specific user, no need to ask again
        if tg_account:
            if (role_type == "student" and tg_account.student_id == db_id) or \
               (role_type == "staff" and tg_account.staff_id == db_id):
                name_to_display = getattr(db_user, 'short_name', None) or getattr(db_user, 'full_name', 'Foydalanuvchi')
                await message.answer(
                    f"👋 Salom, <b>{name_to_display}</b>!\n\n"
                    "✅ <b>Sizning Telegramingiz ro'yxatdan o'tgan!</b>\n\n"
                    "Mobil ilovadan bemalol foydalanishingiz mumkin.",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardRemove()
                )
                return

        # Prepare for phone bind
        await state.update_data(bind_role_type=role_type, bind_db_id=db_id)
        await state.set_state(TelegramBindState.waiting_for_phone)
        
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        name_to_display = getattr(db_user, 'short_name', None) or getattr(db_user, 'full_name', 'Foydalanuvchi')
        role_name_display = "Talaba" if role_type == "student" else "Xodim"
        
        await message.answer(
            f"👋 Assalomu alaykum, <b>{name_to_display}</b> ({role_name_display})!\n\n"
            f"🔐 <b>Avtorizatsiyani yakunlash uchun:</b>\n"
            f"Iltimos, profilingizni himoyalash va Telegram orqali bildirishnomalar/fayllarni qabul qilish uchun quyidagi tugmani bosib <b>telefon raqamingizni yuboring!</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        return

    # Handle Upload Link
    if token.startswith("upload_"):
        session_id = token[7:]
        result = await session.execute(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student), selectinload(TgAccount.staff)))
        tg_account = result.scalar_one_or_none()
        if not tg_account or not (tg_account.student or tg_account.staff):
            await message.answer("❌ Botdan foydalanish uchun avval <b>Tengdosh</b> mobil ilovasiga kiring va 'Telegramga ulanish' tugmasinibosing.", parse_mode="HTML")
            return
            
        from models.states import DocumentAddStates
        await state.set_state(DocumentAddStates.WAIT_FOR_APP_FILE)
        await state.update_data(app_upload_session=session_id)
        
        await message.answer(
            "📁 <b>Hujjat/Faollik yuklash</b>\n\n"
            "Iltimos, rasm yoki faylni shu yerga yuboring.\n"
            "<i>(Maksimal 5 ta gacha rasm yuborishingiz mumkin)</i>",
            parse_mode="HTML"
        )
        return

    # Handle Club Event Upload Link
    if token.startswith("clubevent_"):
        event_id = token[10:]
        result = await session.execute(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student), selectinload(TgAccount.staff)))
        tg_account = result.scalar_one_or_none()
        if not tg_account or not (tg_account.student or tg_account.staff):
            await message.answer("❌ Botdan foydalanish uchun avval <b>Tengdosh</b> mobil ilovasiga kiring va 'Telegramga ulanish' tugmasinibosing.", parse_mode="HTML")
            return
            
        from handlers.student.clubs import ClubEventAddParticipantState
        await state.set_state(ClubEventAddParticipantState.WAIT_FOR_PHOTO)
        await state.update_data(club_event_id=event_id, event_photos=[])
        
        await message.answer(
            "📸 <b>Tadbir rasmlarini yuklash</b>\n\n"
            "Iltimos, tadbirda olingan rasmlarni shu yerga yuboring.\n"
            "<i>(5 tagacha rasm yuborishingiz mumkin)</i>\n\n"
            "Bekor qilish uchun /cancel tugmasini bosing.",
            parse_mode="HTML"
        )
        return

@router.message(TelegramBindState.waiting_for_phone, F.contact)
async def process_phone_binding(message: Message, state: FSMContext, session: AsyncSession):
    """
    Finalizes Telegram Binding after user submits contact.
    """
    contact = message.contact
    user_id = message.from_user.id
    
    # Ensure contact belongs to the user
    if contact.user_id != user_id:
        await message.answer("❌ Iltimos, faqat o'zingizning telefon raqamingizni ulashing.")
        return
        
    phone_number = contact.phone_number
    data = await state.get_data()
    role_type = data.get("bind_role_type")
    db_id = data.get("bind_db_id")
    
    if not role_type or not db_id:
        await state.clear()
        await message.answer("❌ <b>Sessiya tugagan or xatolik yuz berdi.</b>\nIltimos ilovadan qayta ulanish linkini bosing.", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        return
        
    try:
        # Get or create TgAccount
        result = await session.execute(select(TgAccount).where(TgAccount.telegram_id == user_id))
        tg_account = result.scalar_one_or_none()
        
        if not tg_account:
            tg_account = TgAccount(telegram_id=user_id)
            session.add(tg_account)
            
        # Update user profile
        if role_type == "student":
            result = await session.execute(select(Student).where(Student.id == db_id))
            user_profile = result.scalar_one_or_none()
            if user_profile:
                tg_account.student_id = user_profile.id
                tg_account.staff_id = None
                tg_account.current_role = "student"
                user_profile.phone = phone_number
        elif role_type == "staff":
            result = await session.execute(select(Staff).where(Staff.id == db_id))
            user_profile = result.scalar_one_or_none()
            if user_profile:
                tg_account.staff_id = user_profile.id
                tg_account.student_id = None
                tg_account.current_role = "staff"
                user_profile.phone = phone_number
                user_profile.telegram_id = user_id # Legacy sync
                
        if not user_profile:
             await message.answer("❌ Foydalanuvchi tizimda topilmadi.", reply_markup=ReplyKeyboardRemove())
             await state.clear()
             return
             
        await session.commit()
        await state.clear()
        
        name_to_display = getattr(user_profile, 'short_name', None) or getattr(user_profile, 'full_name', 'Foydalanuvchi')
        
        await message.answer(
            f"✅ <b>Tabriklaymiz, {name_to_display}!</b>\n\n"
            f"Sizning Telegramingiz muvaffaqiyatli ulandi (Raqam: {phone_number}).\n"
            f"Endi Mobil ilovadan bemalol foydalanishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Binding Error on phone contact: {e}")
        await message.answer("❌ Tizim xatoligi yuz berdi. Keyinroq urinib ko'ring.", reply_markup=ReplyKeyboardRemove())
        await state.clear()

@router.message(CommandStart())
async def cmd_start_generic(message: Message, state: FSMContext, session: AsyncSession):
    """
    Fallback for non-deep-link start.
    Check if user is Owner/Developer/Admin and show menu.
    """
    user_id = message.from_user.id
    from config import OWNER_TELEGRAM_ID
    from database.models import StaffRole

    # 1. Check if OWNER
    if user_id == int(OWNER_TELEGRAM_ID):
        from keyboards.inline_kb import get_owner_main_menu_inline_kb
        await message.answer(
            f"👋 Assalomu alaykum, <b>Owner</b>!\n\nBoshqaruv menyusi:",
            reply_markup=get_owner_main_menu_inline_kb(),
            parse_mode="HTML"
        )
        return

    # 2. Check Role via TgAccount
    result = await session.execute(
        select(TgAccount)
        .where(TgAccount.telegram_id == user_id)
        .options(selectinload(TgAccount.staff), selectinload(TgAccount.student))
    )
    account = result.scalar_one_or_none()
    
    if account and account.staff:
        # Check privileges
        role = account.staff.role
        if role in [StaffRole.DEVELOPER, StaffRole.OWNER]:
            from keyboards.inline_kb import get_owner_main_menu_inline_kb
            await message.answer(
                f"👋 Assalomu alaykum, <b>{account.staff.full_name}</b>!\n\n(Developer/Owner Maqomi)\nBoshqaruv menyusi:",
                reply_markup=get_owner_main_menu_inline_kb(),
                parse_mode="HTML"
            )
            return
            
        return await message.answer(
            f"👋 Assalomu alaykum, <b>{account.staff.full_name}</b>!\n\n"
            "Siz tizimdan muvaffaqiyatli ro'yxatdan o'tgansiz. Bot orqali markaz qilingan barcha amallarga va ilova funksiyalariga to'liq kirish huquqingiz bor.\n\n"
            "🚪 <i>Hisobdan chiqish uchun /exit buyrug'ini yuboring.</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

    if account and account.student:
        return await message.answer(
            f"👋 Assalomu alaykum, <b>{account.student.full_name}</b>!\n\n"
            "Siz tizimdan muvaffaqiyatli ro'yxatdan o'tgansiz. Faollik va boshqa xizmatlardan foydalanishingiz mumkin.\n\n"
            "🚪 <i>Hisobdan chiqish (logout) uchun /exit buyrug'ini yuboring.</i>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

    # 3. Default Fallback
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Siz botga ulanmagansiz. Botdan foydalanish, dars jadvalingizni olish va "
        "o'z faolliklaringizni yuklash uchun, iltimos, <b>Tengdosh (TalabaHamkor)</b> mobil ilovasiga kiring "
        "va avtorizatsiya vaqtida ko'rsatilgan \"Telegramga ulanish\" xabari orqali ushbu botga kiring.",
        parse_mode="HTML"
    )

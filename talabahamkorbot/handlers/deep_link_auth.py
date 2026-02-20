from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import Student, Staff, TgAccount
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject, session: AsyncSession, state: FSMContext):
    """
    Handles Deep Links:
    1. Authorization Code (Legacy): auth_{uuid}
    2. Upload File: upload_{session_id}
    3. OAuth Login: login__{token} (e.g., login__student_id_123 or login__staff_id_456)
    """
    args = command.args
    user_id = message.from_user.id
    
    if not args:
        return

    # --- 1. LEGACY AUTH FLOW (Mobile -> Bot) ---
    if args.startswith("auth_"):
        from api.auth import verify_login # Import locally to avoid circulars
        auth_uuid = args.replace("auth_", "")
        success = verify_login(auth_uuid, user_id)
        
        if success:
            await message.answer("✅ <b>Tizimga muvaffaqiyatli kirdingiz!</b>\n\nIlovaga qaytishingiz mumkin.")
        else:
            await message.answer("❌ <b>Xatolik!</b>\nLogin sessiyasi eskirgan yoki noto'g'ri.")
        return

    # --- 2. UPLOAD FLOW (Web -> Bot) ---
    elif args.startswith("upload_"):
        session_id = args.replace("upload_", "")
        from database.models import PendingUpload
        from models.states import DocumentAddStates, CertificateAddStates, FeedbackStates, ActivityUploadState
        
        # Find Pending Upload
        pending = await session.get(PendingUpload, session_id)
        if pending:
            # 1. Fetch existing account
            result = await session.execute(select(TgAccount).where(TgAccount.telegram_id == user_id))
            tg_account = result.scalar_one_or_none()

            # Link Account (Auto-Auth)
            if not tg_account:
                tg_account = TgAccount(
                    telegram_id=user_id,
                    student_id=pending.student_id,
                    current_role="student"
                )
                session.add(tg_account)
                await session.commit()
            elif not tg_account.student_id:
                tg_account.student_id = pending.student_id
                tg_account.current_role = "student"
                await session.commit()
            
            # Determine intended state & message
            target_state = DocumentAddStates.WAIT_FOR_APP_FILE
            display_name = pending.title or "Hujjat"
            msg_prefix = f"📎 <b>{display_name}</b> yuklanmoqda...\nIltimos, faylni shu yerga yuboring:"

            if pending.category == "sertifikat":
                target_state = CertificateAddStates.WAIT_FOR_APP_FILE
            elif pending.category == "feedback":
                target_state = FeedbackStates.WAIT_FOR_APP_FILE
                msg_prefix = f"📨 <b>Murojaat uchun fayl yuklash</b>\n\nIlova qilmoqchi bo'lgan faylingizni (Rasm, Video yoki PDF) yuboring:"
            elif pending.category == "Faollik":
                target_state = ActivityUploadState.waiting_for_photo
                msg_prefix = f"📸 <b>Faollik uchun rasm yuklang!</b>\n\nIltimos, faollikka oid rasmlarni yuboring (Maksimal 5 ta):"
            
            await state.set_state(target_state)
            
            await message.answer(
                f"🔗 <b>Hisob Ulandi!</b>\n\n{msg_prefix}",
                parse_mode="HTML"
            )
            return
        else:
            await message.answer("❌ Yuklash sessiyasi topilmadi yoki eskirgan.")
            return

    # --- 3. OAUTH FLOW (Website -> Bot) ---
    elif args.startswith("login__"): # Double underscore separator
        token = args.replace("login__", "")
        
        # Parse Token: student_id_123 or staff_id_456
        parts = token.split("_id_")
        if len(parts) != 2:
            await message.answer("❌ <b>Xatolik!</b>\nNoto'g'ri token formati.")
            return
            
        role_type, db_id = parts[0], parts[1] # role_type: student | staff
        
        if not db_id.isdigit():
            await message.answer("❌ <b>Xatolik!</b>\nID noto'g'ri formatda.")
            return
                
        db_id = int(db_id)
        
        # LINK USER TO DB
        try:
            # 1. Check if TgAccount exists for this telegram_id
            result = await session.execute(select(TgAccount).where(TgAccount.telegram_id == user_id))
            tg_account = result.scalar_one_or_none()
            
            if not tg_account:
                tg_account = TgAccount(telegram_id=user_id)
                session.add(tg_account)
            
            # 2. Link to Student or Staff
            if role_type == "student":
                # Verify Student Exists
                result = await session.execute(select(Student).where(Student.id == db_id))
                student = result.scalar_one_or_none()
                
                if student:
                    tg_account.student_id = student.id
                    tg_account.staff_id = None 
                    await session.commit()
                    
                    await message.answer(
                        f"👋 Salom, <b>{student.short_name or student.full_name}</b>!\n\n"
                        "✅ <b>Sizning Telegramingiz muvaffaqiyatli ulandi.</b>\n\n"
                        "Endi mobil ilovadan bemalol foydalanishingiz mumkin.",
                        parse_mode="HTML"
                    )
                else:
                    await message.answer("❌ Talaba tizimda topilmadi.")
                    
            elif role_type == "staff":
                # Verify Staff Exists
                result = await session.execute(select(Staff).where(Staff.id == db_id))
                staff = result.scalar_one_or_none()
                
                if staff:
                    tg_account.staff_id = staff.id
                    tg_account.student_id = None
                    # Update redundant field in Staff model if needed
                    staff.telegram_id = user_id 
                    
                    await session.commit()
                    await message.answer(f"👋 Salom, <b>{staff.full_name}</b>!\n\n✅ Xodim sifatida ulandi.", parse_mode="HTML")
                else:
                    await message.answer("❌ Xodim tizimda topilmadi.")
                    
            else:
                await message.answer("❌ Noma'lum foydalanuvchi turi.")
                    
        except Exception as e:
            logger.error(f"Deep Link Error: {e}")
            await message.answer("❌ Tizim xatoligi yuz berdi. Keyinroq urinib ko'ring.")

@router.message(CommandStart())
async def cmd_start_generic(message: Message, session: AsyncSession):
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
        .options(selectinload(TgAccount.staff))
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

    # 3. Default Fallback
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Bu bot faqat <b>TalabaHamkor</b> ilovasi orqali fayl yuklash va kirish uchun ishlatiladi.\n\n"
        "📲 Iltimos, mobil ilovadan foydalaning.",
        parse_mode="HTML"
    )

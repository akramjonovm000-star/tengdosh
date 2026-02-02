from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Student, Staff, TgAccount
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject, session: AsyncSession, state: FSMContext):
    """
    Handles Deep Links:
    1. Authorization Code (Legacy): auth_{uuid}
    2. OAuth Login: login__{token} (e.g., login__student_id_123 or login__staff_id_456)
    """
    args = command.args
    user_id = message.from_user.id
    
    if not args:
        return

    # --- 1. LEGACY AUTH FLOW (Mobile -> Bot) ---
    if args.startswith("auth_"):
        from api.auth import verify_login # Import locally to avoid circulars if any
        auth_uuid = args.replace("auth_", "")
        success = verify_login(auth_uuid, user_id)
        
        if success:
            await message.answer("✅ <b>Tizimga muvaffaqiyatli kirdingiz!</b>\n\nIlovaga qaytishingiz mumkin.")
        else:
            await message.answer("❌ <b>Xatolik!</b>\nLogin sessiyasi eskirgan yoki noto'g'ri.")
        return

    # --- 2. OAUTH FLOW (Website -> Bot) ---
    if args.startswith("login__"): # Double underscore separator
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
                    tg_account.staff_id = None # Switch logic: can't be both? Or can? prioritize student
                    await session.commit()
                    
                    from handlers.student.navigation import show_student_main_menu
                    from aiogram.fsm.context import FSMContext
                    # We need state, but this handler doesn't have it in signature. 
                    # Actually, we can add it or just pass None if show_student_main_menu handles it.
                    # show_student_main_menu needs state.
                    
                    # Update signature to include state
                    await show_student_main_menu(message, session, state, text=f"👋 Salom, <b>{student.full_name}</b>!\n\n✅ Sizning Telegram profilingiz HEMIS akkauntingizga muvaffaqiyatli ulandi.\n\nQuyidagilardan birini tanlang:")
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
                    await message.answer(f"👋 Salom, <b>{staff.full_name}</b>!\n\n✅ Sizning Telegram profilingiz Xodim sifatida ulandi.")
                else:
                    await message.answer("❌ Xodim tizimda topilmadi.")
                    
            else:
                 await message.answer("❌ Noma'lum foydalanuvchi turi.")
                 
        except Exception as e:
            logger.error(f"Deep Link Error: {e}")
            await message.answer("❌ Tizim xatoligi yuz berdi. Keyinroq urinib ko'ring.")

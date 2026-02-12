from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, Club, Student, Election, Staff, StaffRole
from keyboards.inline_kb import get_student_main_menu_kb

router = Router()

async def show_student_main_menu(target, session: AsyncSession, state: FSMContext, text: str = None, banner_index: int = 0):
    """
    Centralized function to show student main menu.
    target: CallbackQuery or Message
    """
    from aiogram.types import CallbackQuery, Message, InputMediaPhoto
    from database.models import Banner
    
    user_id = target.from_user.id
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id))
    
    is_election_admin = False
    has_active_election = False
    led_clubs = []
    
    if account:
        if account.staff_id:
            led_clubs = (await session.execute(select(Club).where(Club.leader_id == account.staff_id))).scalars().all()
        
        if account.student_id:
            student = await session.get(Student, account.student_id)
            if student:
                from utils.student_utils import get_election_info
                is_election_admin, has_active_election = await get_election_info(student, session)
        
    # Developer check
    is_developer = False
    result = await session.execute(
        select(Staff).where(
            Staff.telegram_id == user_id,
            Staff.role == StaffRole.DEVELOPER,
            Staff.is_active == True
        )
    )
    if result.scalar_one_or_none():
        is_developer = True
    
    # --- FETCH BANNERS ---
    # We fetch ALL active banners to support Carousel
    banners = (await session.execute(select(Banner).where(Banner.is_active == True).order_by(Banner.id.desc()))).scalars().all()
    total_banners = len(banners)
    
    # Validate index
    if banner_index >= total_banners:
        banner_index = 0
    
    current_banner = banners[banner_index] if banners else None

    # Delete instruction message if exists
    data = await state.get_data()
    instr_id = data.get("reply_instruction_msg_id")
    if instr_id:
        try:
            bot = target.bot if hasattr(target, 'bot') else target.message.bot
            await bot.delete_message(chat_id=user_id, message_id=instr_id)
        except:
            pass

    if not text:
        text = "🎓 <b>Talaba asosiy menyusi:</b>"
        
    kb = get_student_main_menu_kb(
        led_clubs=led_clubs, 
        is_election_admin=is_election_admin, 
        has_active_election=has_active_election,
        is_developer=is_developer,
        banner_index=banner_index,
        total_banners=total_banners
    )
    
    message = target.message if isinstance(target, CallbackQuery) else target
    
    # --- SENDING LOGIC (Text vs Photo) ---
    try:
        if current_banner:
            # Prefer sending Photo
            caption = text
            if current_banner.link:
                caption += f"\n\n🔗 <a href='{current_banner.link}'>Batafsil ma'lumot</a>"
            
            # If editing existing message
            if isinstance(target, CallbackQuery):
                # If message is already a photo, edit media
                if message.photo:
                     try:
                         media = InputMediaPhoto(media=current_banner.image_file_id, caption=caption, parse_mode="HTML")
                         await message.edit_media(media=media, reply_markup=kb)
                     except Exception as e:
                         # Likely file_id invalid or same content
                         if "file reference" in str(e) or "file not found" in str(e) or "wrong file identifier" in str(e):
                             # Fallback to Text if image fails
                             await message.delete()
                             await message.answer(f"🖼 [Rasm yuklanmadi: {current_banner.id}]\n\n{text}", reply_markup=kb, parse_mode="HTML")
                         else:
                             # Ignore "message is not modified"
                             pass
                else:
                     # Was text, delete and send photo 
                     await message.delete()
                     try:
                        await message.answer_photo(photo=current_banner.image_file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
                     except:
                        # Fallback
                        await message.answer(f"🖼 [Rasm yuklanmadi: {current_banner.id}]\n\n{text}", reply_markup=kb, parse_mode="HTML")
            else:
                # Message provided (Command)
                try:
                    await message.answer_photo(photo=current_banner.image_file_id, caption=caption, reply_markup=kb, parse_mode="HTML")
                except:
                     await message.answer(f"🖼 [Rasm yuklanmadi: {current_banner.id}]\n\n{text}", reply_markup=kb, parse_mode="HTML")

        else:
            # Fallback to Text
            if isinstance(target, CallbackQuery):
                if message.photo:
                     # Was photo, delete and send text
                     await message.delete()
                     await message.answer(text, reply_markup=kb, parse_mode="HTML")
                else:
                     await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            else:
                await message.answer(text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        # Fallback if something fails (e.g. file_id invalid)
        try:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
        except:
            pass


@router.callback_query(F.data == "go_student_home")
async def cb_go_student_home(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    # Remove Reply Keyboard if exists
    try:
        temp_msg = await call.message.answer("...", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except:
        pass

    await show_student_main_menu(call, session, state)
    await call.answer()


@router.callback_query(F.data.startswith("main_banner:"))
async def cb_main_banner_nav(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        idx = int(call.data.split(":")[1])
        await show_student_main_menu(call, session, state, banner_index=idx)
    except Exception as e:
        await call.answer("Xatolik!")
        
@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()

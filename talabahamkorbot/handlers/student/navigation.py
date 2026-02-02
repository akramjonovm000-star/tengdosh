from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, Club, Student, Election
from keyboards.inline_kb import get_student_main_menu_kb

router = Router()

async def show_student_main_menu(target, session: AsyncSession, state: FSMContext, text: str = None):
    """
    Centralized function to show student main menu.
    target: CallbackQuery or Message
    """
    from aiogram.types import CallbackQuery, Message
    
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
        
    kb = get_student_main_menu_kb(led_clubs=led_clubs, is_election_admin=is_election_admin, has_active_election=has_active_election)
    
    message = target.message if isinstance(target, CallbackQuery) else target
    
    try:
        if isinstance(target, CallbackQuery):
            await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        try:
            await message.delete()
        except:
            pass
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "go_student_home")
async def cb_go_student_home(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    # Remove Reply Keyboard if exists (hacky way: send msg and delete)
    try:
        temp_msg = await call.message.answer("...", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except:
        pass

    await show_student_main_menu(call, session, state)
    await call.answer()

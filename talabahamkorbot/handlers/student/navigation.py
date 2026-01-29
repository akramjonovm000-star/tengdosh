from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, Club
from keyboards.inline_kb import get_student_main_menu_kb

router = Router()

@router.callback_query(F.data == "go_student_home")
async def cb_go_student_home(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    # Fetch user account to check for Led Clubs
    tg_id = call.from_user.id
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
    
    led_clubs = []
    if account and account.staff_id:
        led_clubs = (await session.execute(select(Club).where(Club.leader_id == account.staff_id))).scalars().all()
        
    # Remove Reply Keyboard if exists (hacky way: send msg and delete)
    try:
        temp_msg = await call.message.answer("...", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except:
        pass

    # Delete instruction message if exists
    data = await state.get_data()
    instr_id = data.get("reply_instruction_msg_id")
    if instr_id:
        try:
            await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=instr_id)
        except:
            pass

    text = "🎓 <b>Talaba asosiy menyusi:</b>"
    kb = get_student_main_menu_kb(led_clubs=led_clubs)
    
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.delete()
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

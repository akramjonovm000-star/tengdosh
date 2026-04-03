from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database.models import DormitoryIssue, TgAccount
# Reuse HousingAddStates or create DormIssueStates
from aiogram.fsm.state import State, StatesGroup
import logging

class DormIssueStates(StatesGroup):
    waiting_for_images = State()

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart(deep_link=True, magic=F.args.regexp(r"report_dorm_issue_(\d+)")))
async def cmd_start_dorm_issue_upload(message: Message, command: CommandObject, session: AsyncSession, state: FSMContext):
    """
    Handles Deep Link: report_dorm_issue_{id}
    """
    issue_id = int(command.args.split("_")[-1])
    user_id = message.from_user.id
    
    # Check if this issue belong to the student
    result = await session.execute(
        select(DormitoryIssue)
        .join(TgAccount, TgAccount.student_id == DormitoryIssue.student_id)
        .where(DormitoryIssue.id == issue_id)
        .where(TgAccount.telegram_id == user_id)
    )
    issue = result.scalar_one_or_none()
    
    if not issue:
        await message.answer("❌ <b>Xatolik!</b>\nUshbu murojaat topilmadi yoki sizga tegishli emas.", parse_mode="HTML")
        return

    await state.set_state(DormIssueStates.waiting_for_images)
    await state.update_data(current_dorm_issue_id=issue_id, dorm_issue_images=[])
    
    await message.answer(
        f"🛠 <b>Yotoqxona nosozligi: {issue.category}</b>\n\n"
        "Iltimos, nosozlik tasvirlangan rasmlarni shu yerga yuboring.\n"
        "<i>(3 tagacha rasm yuborishingiz mumkin)</i>\n\n"
        "Yuklab bo'lgach, ilovaga qaytib murojaat holatini kuzatib borishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(DormIssueStates.waiting_for_images, F.photo)
async def process_dorm_issue_photo(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    issue_id = data.get("current_dorm_issue_id")
    images = data.get("dorm_issue_images", [])
    
    if len(images) >= 3:
        await message.answer("⚠️ Maksimal 3 ta rasm yuklash mumkin.")
        return

    file_id = message.photo[-1].file_id
    images.append(file_id)
    await state.update_data(dorm_issue_images=images)
    
    await session.execute(
        update(DormitoryIssue)
        .where(DormitoryIssue.id == issue_id)
        .values(image_urls=images)
    )
    await session.commit()
    
    if len(images) == 1:
        await message.answer(f"✅ 1-rasm qabul qilindi. Yana {3 - len(images)} tagacha yuborishingiz mumkin.")
    elif len(images) == 3:
        await message.answer("✅ Barcha 3 ta rasm muvaffaqiyatli yuklandi! Ilovada murojaat holatini tekshirishingiz mumkin.")
        await state.clear()

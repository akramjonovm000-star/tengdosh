from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database.models import MarketItem, TgAccount
from models.states import HousingAddStates
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart(deep_link=True, magic=F.args.regexp(r"add_housing_(\d+)")))
async def cmd_start_housing_upload(message: Message, command: CommandObject, session: AsyncSession, state: FSMContext):
    """
    Handles Deep Link: add_housing_{item_id}
    """
    item_id = int(command.args.split("_")[-1])
    user_id = message.from_user.id
    
    # Check if this item belongs to the student
    result = await session.execute(
        select(MarketItem)
        .join(TgAccount, TgAccount.student_id == MarketItem.student_id)
        .where(MarketItem.id == item_id)
        .where(TgAccount.telegram_id == user_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        await message.answer("❌ <b>Xatolik!</b>\nUshbu e'lon topilmadi yoki sizga tegishli emas.", parse_mode="HTML")
        return

    await state.set_state(HousingAddStates.waiting_for_images)
    await state.update_data(current_housing_id=item_id, housing_images=[])
    
    await message.answer(
        f"🏠 <b>'{item.title}'</b> e'loni uchun rasm yuklash\n\n"
        "Iltimos, turarjoy rasmlarini shu yerga yuboring.\n"
        "<i>(Maksimal 5 tagacha rasm yuborishingiz mumkin. Rasmlar albom ko'rinishida bo'lsa ham qabul qilinadi)</i>\n\n"
        "Yuklab bo'lgach, ilovaga qaytib e'loningizni tekshirishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(HousingAddStates.waiting_for_images, F.photo)
async def process_housing_photo(message: Message, state: FSMContext, session: AsyncSession):
    """
    Receives photos for the listing.
    """
    data = await state.get_data()
    item_id = data.get("current_housing_id")
    images = data.get("housing_images", [])
    
    if len(images) >= 5:
        await message.answer("⚠️ Maksimal 5 ta rasm yuklash mumkin. Avvalgi rasmlar saqlandi.")
        return

    # Get the highest resolution photo
    file_id = message.photo[-1].file_id
    images.append(file_id)
    await state.update_data(housing_images=images)
    
    # Update DB immediately for each photo (or wait for confirmation, but immediate is simpler for "Telegram Cloud" requirement)
    # We update the image_urls (JSONB)
    await session.execute(
        update(MarketItem)
        .where(MarketItem.id == item_id)
        .values(image_urls=images)
    )
    await session.commit()
    
    if len(images) == 1:
        await message.answer(f"✅ 1-rasm qabul qilindi. Yana {5 - len(images)} tagacha yuborishingiz mumkin.")
    elif len(images) == 5:
        await message.answer("✅ Barcha 5 ta rasm muvaffaqiyatli yuklandi! Ilovada e'loningizni ko'rishingiz mumkin.")
        await state.clear()
    else:
        # For albums, we don't want to spam messages, but aiogram handles media groups as separate messages unless using a special middleware.
        # For simplicity, we just send a confirmation.
        pass

@router.message(HousingAddStates.waiting_for_images, F.media_group_id)
async def process_housing_album(message: Message, state: FSMContext, session: AsyncSession):
    """
    Handles albums (Media groups). Note: This is called for EACH message in the album.
    """
    # This will be handled by the F.photo handler above as each media group message has a photo.
    # If we wanted to be more efficient, we'd use a middleware, but this works fine.
    pass

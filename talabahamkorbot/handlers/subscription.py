from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(call: CallbackQuery):
    """
    Agar middleware o'tkazib yuborgan bo'lsa, demak foydalanuvchi a'zo bo'lgan.
    Shunchaki xabarni o'chirib, "Rahmat" deymiz.
    """
    await call.message.delete()
    await call.message.answer("✅ Rahmat! Botdan foydalanishingiz mumkin.")
    await call.answer()

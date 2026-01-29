from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "soon")
async def not_ready_yet(call: CallbackQuery):
    await call.answer("⚙️ Ushbu bo‘lim tez orada ishga tushadi!", show_alert=True)

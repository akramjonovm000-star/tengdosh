import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student
from keyboards.inline_kb import get_student_main_menu_kb

router = Router()
logger = logging.getLogger(__name__)

# --- Keyboards ---
def get_premium_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lov qilish (Click/Payme)", callback_data="prem_pay_click")],
        [InlineKeyboardButton(text="📄 Chek yuborish (Manual)", callback_data="prem_pay_manual")],
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="go_student_home")]
    ])

def get_manual_pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Chekni yuklash", callback_data="prem_upload_proof")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_premium_menu")]
    ])

# --- Handlers ---

@router.callback_query(F.data == "student_premium_menu")
async def show_premium_menu(call: CallbackQuery, session: AsyncSession):
    from utils.student_utils import get_student_by_tg
    student = await get_student_by_tg(call.from_user.id, session)
    
    if not student:
        return await call.answer("Student topilmadi", show_alert=True)
        
    status = "❌ Oddiy (Free)"
    expiry = "Cheklanmagan"
    
    if student.is_premium:
        status = "✅ PREMIUM"
        if student.premium_expiry:
            expiry = student.premium_expiry.strftime("%d.%m.%Y")
        else:
            expiry = "Cheksiz"
            
    msg = (
        f"💎 <b>Premium Obuna</b>\n\n"
        f"Hozirgi holatingiz: <b>{status}</b>\n"
        f"Amal qilish muddati: <b>{expiry}</b>\n\n"
        "<b>Premium imkoniyatlari:</b>\n"
        "✅ AI Yordamchi (Chat & Konspekt)\n"
        "✅ Ijtimoiy Faollik moduli\n"
        "✅ Kengaytirilgan Statistika\n"
        "✅ Reklamasiz rejim\n\n"
        "<b>Tariflar:</b>\n"
        "• Bir oylik — 10,000 so'm\n"
        "• Uch oylik — 25,000 so'm\n"
        "• Olti oylik — 40,000 so'm\n"
        "• Bir yillik — 70,000 so'm\n\n"
        "ℹ️ <i>Obunani sotib olish uchun mobil ilovadan foydalaning.</i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Ilovani ochish", url="https://talabahamkor.uz/app")], # Placeholder link
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="go_student_home")]
    ])
    
    await call.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "prem_pay_click")
async def pay_click(call: CallbackQuery):
    await call.answer("🛠 Click tez orada ishga tushadi!", show_alert=True)

@router.callback_query(F.data == "prem_pay_manual")
async def pay_manual(call: CallbackQuery):
    msg = (
        "💳 <b>To'lov uchun karta:</b>\n\n"
        "<code>8600 1234 5678 9012</code>\n"
        "Ism: <b>Toshmat E.</b>\n\n"
        "Summa: <b>10,000 so'm</b>\n\n"
        "To'lov qilgach, chekni (skrinshot) shu yerga yuborish uchun pastdagi tugmani bosing."
    )
    await call.message.edit_text(msg, reply_markup=get_manual_pay_kb(), parse_mode="HTML")

@router.callback_query(F.data == "prem_upload_proof")
async def ask_proof(call: CallbackQuery):
    await call.message.edit_text(
        "📸 <b>Chekni yuboring:</b>\n\n"
        "Iltimos, to'lov chekini rasm holatida yuboring.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data="student_premium_menu")]])
    )
    # Here we would set state, but keeping it simple for now or assuming global photo handler catches it.

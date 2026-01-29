import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.states import MobilePushStates
from services.notification_service import NotificationService
from database.models import Staff, TgAccount, StaffRole
from keyboards.inline_kb import get_rahbariyat_main_menu_kb, get_dekanat_main_menu_kb

router = Router()
logger = logging.getLogger(__name__)

# ============================================================
# 1. Start Workflow
# ============================================================
@router.callback_query(F.data.in_({"rh_mobile_push", "dk_mobile_push"}))
async def start_mobile_push(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    
    # Store trigger source for back button logic
    await state.update_data(source=call.data)
    await state.set_state(MobilePushStates.waiting_title)
    
    await call.message.edit_text(
        "📲 <b>Mobile App Push - Xabar yuborish</b>\n\n"
        "Ushbu xabar ilova o'rnatgan <b>barcha foydalanuvchilarga</b> push-bildirishnoma sifatida boradi.\n\n"
        "✍️ Birinchi bo'lib xabar <b>SARLAVHASINI</b> (Title) yuboring:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="push_cancel")]
        ])
    )
    await call.answer()

# ============================================================
# 2. Receive Title
# ============================================================
@router.message(MobilePushStates.waiting_title)
async def process_push_title(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Iltimos, faqat matn ko'rinishida sarlavha yuboring.")
        return
        
    await state.update_data(title=message.text)
    await state.set_state(MobilePushStates.waiting_body)
    
    await message.answer(
        "✅ Sarlavha qabul qilindi.\n\n"
        "✍️ Endi xabar <b>MATNINI</b> (Body) yuboring:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="push_back_to_title")]
        ])
    )

# ============================================================
# 3. Receive Body & Show Preview
# ============================================================
@router.message(MobilePushStates.waiting_body)
async def process_push_body(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Iltimos, faqat matn ko'rinishida xabar yuboring.")
        return
        
    await state.update_data(body=message.text)
    data = await state.get_data()
    
    preview_text = (
        "👀 <b>XABAR PREVYUSI:</b>\n\n"
        f"📌 <b>Sarlavha:</b> {data['title']}\n"
        f"📝 <b>Matn:</b> {data['body']}\n\n"
        "⚠️ Diqqat: 'Tasdiqlash' tugmasini bossangiz, xabar bir zumda barcha foydalanuvchilarga yuboriladi!"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash va Yuborish", callback_data="push_confirm_send")],
        [InlineKeyboardButton(text="✍️ Matnni o'zgartirish", callback_data="push_back_to_body")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="push_cancel")]
    ])
    
    await state.set_state(MobilePushStates.confirming)
    await message.answer(preview_text, parse_mode="HTML", reply_markup=kb)

# ============================================================
# 4. Confirm & Dispatch
# ============================================================
@router.callback_query(MobilePushStates.confirming, F.data == "push_confirm_send")
async def confirm_push_send(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    
    # Security check: ensure staff still has right
    staff = await session.scalar(select(Staff).join(TgAccount).where(TgAccount.telegram_id == call.from_user.id))
    if not staff or staff.role not in {StaffRole.RAHBARIYAT, StaffRole.DEKANAT}:
         await call.answer("❌ Sizda bu amalga ruxsat yo'q.", show_alert=True)
         return

    # Trigger Global Broadcast (CELERY)
    NotificationService.run_broadcast.delay(
        title=data['title'],
        body=data['body'],
        data={"type": "announcement"}
    )
    
    await state.clear()
    
    success_text = (
        "🚀 <b>Broadcast ishga tushirildi!</b>\n\n"
        "Xabarlar navbatga qo'yildi va bir necha daqiqa ichida barcha qurilmalarga yetib boradi."
    )
    
    # Decide which menu to show back
    kb = get_rahbariyat_main_menu_kb() if staff.role == StaffRole.RAHBARIYAT else get_dekanat_main_menu_kb()
    
    await call.message.edit_text(success_text, parse_mode="HTML", reply_markup=kb)
    await call.answer("Yuborildi!")

# ============================================================
# 5. Helper Callbacks (Back/Cancel)
# ============================================================
@router.callback_query(F.data == "push_cancel")
async def cancel_push(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    staff = await session.scalar(select(Staff).join(TgAccount).where(TgAccount.telegram_id == call.from_user.id))
    kb = get_rahbariyat_main_menu_kb() if staff and staff.role == StaffRole.RAHBARIYAT else get_dekanat_main_menu_kb()
    
    await call.message.edit_text("❌ Push-xabar bekor qilindi.", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "push_back_to_title")
async def back_to_title(call: CallbackQuery, state: FSMContext):
    await state.set_state(MobilePushStates.waiting_title)
    await call.message.edit_text("✍️ Xabar <b>SARLAVHASINI</b> (Title) yozing:", parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "push_back_to_body")
async def back_to_body(call: CallbackQuery, state: FSMContext):
    await state.set_state(MobilePushStates.waiting_body)
    await call.message.edit_text("✍️ Xabar <b>MATNINI</b> (Body) yozing:", parse_mode="HTML")
    await call.answer()

import logging
import csv
import asyncio
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

from utils.owner_stats import get_owner_dashboard_text

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, func, distinct, case
from sqlalchemy.ext.asyncio import AsyncSession

from config import OWNER_TELEGRAM_ID

from database.models import TutorGroup, UserActivityImage, TgAccount, StudentFeedback, UserAppeal, UserDocument


from database.models import (
    Staff,
    StaffRole,
    University,
    Faculty,
    Student,
    Student,
    Banner,
    Announcement,
)

from models.states import OwnerStates

from keyboards.inline_kb import (
    get_start_role_inline_kb,
    get_owner_main_menu_inline_kb,
    get_back_inline_kb,
    get_university_actions_kb,
    get_import_confirm_kb,
    get_import_retry_kb,
    get_owner_developers_kb,
    get_dev_add_cancel_kb,
    get_numbered_universities_kb,
    get_owner_announcement_menu_kb,
    get_active_announcements_kb,
    get_announcement_actions_kb,
    get_owner_banner_menu_kb,
    get_banner_list_kb,
    get_banner_actions_kb,
)

logger = logging.getLogger(__name__)
router = Router()


# -------------------------------------------------------------
#                 OWNER HUQUQINI TEKSHIRISH
# -------------------------------------------------------------
async def _ensure_owner(event: Message | CallbackQuery, session: AsyncSession) -> Staff | None:
    """
    Owner yoki developer ekanligini tekshiruvchi funksiya.
    """
    user_id = event.from_user.id

    # Egasi bo‘lsa → to‘g‘ridan to‘g‘ri owner
    if user_id == OWNER_TELEGRAM_ID:
        return Staff(id=0, full_name="Owner", role=StaffRole.OWNER, is_active=True)

    # Boshqa owner/developer xodimni tekshiramiz
    result = await session.execute(
        select(Staff).where(
            Staff.telegram_id == user_id,
            Staff.is_active.is_(True),
            Staff.role.in_([StaffRole.OWNER, StaffRole.DEVELOPER]),
        )
    )
    staff = result.scalar_one_or_none()

    if staff:
        return staff

    # Ruxsat yo‘q
    msg = event.message if isinstance(event, CallbackQuery) else event
    await msg.answer(
        "❌ Sizda owner/developer huquqlari mavjud emas.\n\n"
        "Bosh menyuga qayting va mos rol bilan tizimga kiring.",
        reply_markup=get_start_role_inline_kb(),
    )
    return None


# -------------------------------------------------------------
#                OWNER ASOSIY MENYUSI (INLINE)
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_menu")
async def cb_owner_main_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(OwnerStates.main_menu)
    
    text = await get_owner_dashboard_text(session)

    await call.message.edit_text(
        text,
        reply_markup=get_owner_main_menu_inline_kb(),
        parse_mode="HTML"
    )
    await call.answer()

# ==============================================================
#        📌 OWNER — OTM VA FAKULTETLAR BLOKI (TARTIBLI)
# ==============================================================

from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from pathlib import Path
from io import StringIO
import csv
import logging

from database.models import University, Faculty, Staff, Student, StaffRole
from models.states import OwnerStates
from keyboards.inline_kb import (
    get_back_inline_kb,
    get_university_actions_kb,
    get_import_retry_kb
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------
# 1) 📌 OTM VA FAKULTETLAR — KIRISH
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_universities")
async def cb_owner_universities(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    await state.clear()  # ortga tugma ishlashi uchun state tozalaymiz

    staff = await _ensure_owner(call, session)
    if not staff:
        return

    # Fetch all universities
    result = await session.execute(select(University).order_by(University.id))
    universities = result.scalars().all()

    if not universities:
        await call.message.edit_text(
            "🏛 OTMlar ro'yxati bo'sh.\n\n"
            "Yangi OTM qo'shish uchun <b>uni_code</b> kiriting.",
            parse_mode="HTML",
            reply_markup=get_back_inline_kb("owner_menu")
        )
        await state.set_state(OwnerStates.entering_uni_code)
        await call.answer()
        return

    text = "🏛 <b>Mavjud universitetlar:</b>\n\n"
    for i, uni in enumerate(universities, 1):
        text += f"{i}. {uni.name} (<code>{uni.uni_code}</code>)\n"

    text += "\nSozlash uchun raqamlardan birini tanlang:"

    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_numbered_universities_kb(universities)
    )

    await call.answer()


@router.callback_query(F.data.startswith("owner_uni_select:"))
async def owner_select_uni(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Handles numeric selection of a university.
    """
    uni_id = int(call.data.split(":")[1])
    uni = await session.get(University, uni_id)
    
    if not uni:
        return await call.answer("❌ OTM topilmadi.", show_alert=True)

    await state.update_data(university_id=uni.id, uni_code=uni.uni_code)
    await state.set_state(OwnerStates.university_selected)

    await call.message.edit_text(
        f"✅ <b>{uni.name}</b> tanlandi!\n\n"
        "Quyidagi bo‘limlardan birini tanlang:",
        reply_markup=get_university_actions_kb(uni.id),
        parse_mode="HTML",
    )
    await call.answer()

    # -------------------------------------------------------------
#          OTM KODINI QABUL QILISH (OwnerStates.entering_uni_code)
# -------------------------------------------------------------
@router.message(OwnerStates.entering_uni_code)
async def owner_enter_uni_code(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    uni_code = message.text.strip()

    # Bazadan qidiramiz (ilike -> case insensitive)
    result = await session.execute(
        select(University).where(University.uni_code.ilike(uni_code))
    )
    uni = result.scalar_one_or_none()

    if not uni:
        await message.answer(
            "❌ Bunday OTM topilmadi.\n"
            "Iltimos, to‘g‘ri <b>uni_code</b> kiriting.",
            parse_mode="HTML",
        )
        return

    # Statega yozamiz
    await state.update_data(university_id=uni.id, uni_code=uni.uni_code)
    await state.set_state(OwnerStates.university_selected)

    await message.answer(
        f"✅ <b>{uni.name}</b> topildi!\n\n"
        "Endi quyidagi bo‘limlardan birini tanlang:",
        reply_markup=get_university_actions_kb(uni.id),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("owner_view_uni:"))
async def cb_owner_view_university(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    university_id = int(call.data.split(":")[1])
    uni = await session.get(University, university_id)
    if not uni:
        return await call.answer("❌ OTM topilmadi.", show_alert=True)
        
    await state.update_data(university_id=uni.id, uni_code=uni.uni_code)
    await state.set_state(OwnerStates.university_selected)

    await call.message.edit_text(
        f"✅ <b>{uni.name}</b>\n\n"
        "Quyidagi bo‘limlardan birini tanlang:",
        reply_markup=get_university_actions_kb(uni.id),
        parse_mode="HTML",
    )
    await call.answer()


    
# =============================================================
#         📌  KANAL MAJBURIYATI MODULI (TO‘G‘RI ISHLAYDIGAN YANGI VERSIYA)
# =============================================================

from keyboards.inline_kb import (
    get_channel_menu_kb,
    get_channel_save_confirm_kb,
    get_channel_remove_confirm_kb,
    get_retry_channel_forward_kb,
    get_channel_add_confirm_kb
)

# -------------------------------------------------------------
#   Owner → Kanal majburiyati menyusi
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("uni_channel_menu:"))
async def cb_uni_channel_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    _, uni_id = call.data.split(":")
    university_id = int(uni_id)

    result = await session.execute(select(University).where(University.id == university_id))
    university = result.scalar_one_or_none()

    if not university:
        return await call.message.edit_text(
            "❌ Universitet topilmadi.",
            reply_markup=get_back_inline_kb("owner_universities"),
        )

    await state.update_data(university_id=university_id)

    await call.message.edit_text(
        f"🏛 <b>{university.name}</b>\n\n"
        f"📌 Majburiy kanal: <code>{university.required_channel or 'YO‘Q'}</code>\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=get_channel_menu_kb(university_id),
    )
    await call.answer()


# -------------------------------------------------------------
#       ➕ Kanal qo‘shish / yangilash → Forward so‘rash
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("channel_menu_add:"))
async def cb_channel_add(call: CallbackQuery, state: FSMContext):

    _, uni_id = call.data.split(":")
    university_id = int(uni_id)

    await state.update_data(university_id=university_id)
    await state.set_state(OwnerStates.waiting_channel_forward)

    await call.message.edit_text(
        "📌 Majburiy kanal qo‘shish uchun:\n\n"
        "👉 Kanal ichidagi <b>istalgan xabarni botga forward</b> qiling.",
        reply_markup=get_back_inline_kb(f"uni_channel_menu:{university_id}"),
    )
    await call.answer()


# =============================================================
#   🔥 Forwardni qabul qilish — to‘g‘ri 1 dona handler
# =============================================================
@router.message(
    OwnerStates.waiting_channel_forward,
    F.forward_origin | F.forward_from_chat | F.sender_chat
)
async def process_forwarded_channel(message: Message, state: FSMContext):

    channel_id = None
    channel_title = None

    # --- Yangi forward turi ---
    if message.forward_origin and hasattr(message.forward_origin, "chat"):
        chat = message.forward_origin.chat
        if chat and chat.type == "channel":
            channel_id = chat.id
            channel_title = chat.title

    # --- Eski forward turi ---
    elif message.forward_from_chat and message.forward_from_chat.type == "channel":
        channel_id = message.forward_from_chat.id
        channel_title = message.forward_from_chat.title

    # --- sender_chat ---
    elif message.sender_chat and message.sender_chat.type == "channel":
        channel_id = message.sender_chat.id
        channel_title = message.sender_chat.title

    # ❌ Forward kanal emas
    if not channel_id:
        return await message.answer(
            "❌ Forward qilingan xabar <b>kanaldan emas</b>.",
            reply_markup=get_retry_channel_forward_kb(),
        )

    # 🔥 Bot adminligini tekshirish
    try:
        me = await message.bot.me()
        member = await message.bot.get_chat_member(channel_id, me.id)

        if member.status not in ("administrator", "creator"):
            return await message.answer(
                "❌ Bot kanalga admin emas.\n"
                "Botni kanalga admin qiling va qayta urinib ko‘ring.",
                reply_markup=get_retry_channel_forward_kb(),
            )

    except Exception:
        return await message.answer(
            "❌ Bot kanal bilan aloqa o‘rnata olmadi.\n"
            "Ehtimol, bot kanalga qo‘shilmagan yoki admin emas.",
            reply_markup=get_retry_channel_forward_kb(),
        )

    # ✔ Saqlashga tayyor
    await state.update_data(channel_id=channel_id, channel_title=channel_title)
    await state.set_state(OwnerStates.confirming_channel_save)

    await message.answer(
        f"📡 Kanal topildi!\n\n"
        f"🏷 <b>{channel_title}</b>\n"
        f"🆔 <code>{channel_id}</code>\n\n"
        "Ushbu kanalni majburiy kanal sifatida saqlaysizmi?",
        reply_markup=get_channel_save_confirm_kb(),
    )


# =============================================================
#          ❗ Forward emas → fallback
# =============================================================
@router.message(
    OwnerStates.waiting_channel_forward,
    ~F.forward_origin & ~F.forward_from_chat & ~F.sender_chat
)
async def fallback_not_forward(message: Message):
    await message.answer(
        "❌ Bu forward emas.\n"
        "Iltimos, kanal ichidagi xabarni forward qiling.",
        reply_markup=get_retry_channel_forward_kb(),
    )


# =============================================================
#     📌 “Tasdiqlayman” → Kanalni bazaga yozish
# =============================================================
@router.callback_query(F.data == "channel_save_yes")
async def cb_channel_save_yes(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    data = await state.get_data()
    university_id = data.get("university_id")
    channel_id = data.get("channel_id")

    result = await session.execute(select(University).where(University.id == university_id))
    university = result.scalar_one_or_none()

    university.required_channel = str(channel_id)
    await session.commit()

    await state.set_state(OwnerStates.university_selected)

    await call.message.edit_text(
        "✅ Kanal majburiyati saqlandi!",
        reply_markup=get_back_inline_kb("owner_universities"),
    )
    await call.answer()


# -------------------------------------------------------------
#     ❌ Bekor qilish
# -------------------------------------------------------------
@router.callback_query(F.data == "channel_save_no")
async def cb_channel_save_no(call: CallbackQuery, state: FSMContext):

    await state.set_state(OwnerStates.university_selected)
    await call.message.edit_text(
        "ℹ️ Saqlash bekor qilindi.",
        reply_markup=get_back_inline_kb("owner_universities"),
    )
    await call.answer()


# -------------------------------------------------------------
#         ❗ “Qayta urinaman”
# -------------------------------------------------------------
@router.callback_query(F.data == "retry_forward")
async def cb_retry_forward(call: CallbackQuery, state: FSMContext):

    university_id = (await state.get_data()).get("university_id")

    await state.set_state(OwnerStates.waiting_channel_forward)

    await call.message.edit_text(
        "📌 Qayta urinib ko‘ring.\n"
        "👉 Kanal ichidagi xabarni forward yuboring.",
        reply_markup=get_back_inline_kb(f"uni_channel_menu:{university_id}"),
    )
    await call.answer()


# -------------------------------------------------------------
#      ➖ Kanalni o‘chirish
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("channel_menu_del:"))
async def cb_channel_delete_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    _, uni_id = call.data.split(":")
    university_id = int(uni_id)

    result = await session.execute(select(University).where(University.id == university_id))
    university = result.scalar_one_or_none()

    if not university.required_channel:
        return await call.message.edit_text(
            "ℹ️ Majburiy kanal mavjud emas.",
            reply_markup=get_back_inline_kb("owner_universities"),
        )

    await state.update_data(university_id=university_id)
    await state.set_state(OwnerStates.confirming_channel_delete)

    await call.message.edit_text(
        f"⚠️ Joriy kanal: <code>{university.required_channel}</code>\n"
        "Haqiqatan ham o‘chirilsinmi?",
        reply_markup=get_channel_remove_confirm_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "channel_remove_yes")
async def cb_channel_remove_yes(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    uni_id = (await state.get_data()).get("university_id")

    result = await session.execute(select(University).where(University.id == uni_id))
    university = result.scalar_one_or_none()

    university.required_channel = None
    await session.commit()

    await call.message.edit_text(
        "🗑 Kanal o‘chirildi.",
        reply_markup=get_back_inline_kb("owner_universities"),
    )
    await call.answer()


@router.callback_query(F.data == "channel_remove_no")
async def cb_channel_remove_no(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "ℹ️ O‘chirish bekor qilindi.",
        reply_markup=get_back_inline_kb("owner_universities"),
    )
    await call.answer()




# -------------------------------------------------------------
#                 IMPORT BO‘LIMI (ESKI STUB)
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_import")
async def cb_owner_import(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):

    staff = await _ensure_owner(call, session)
    if not staff:
        return

    await state.set_state(OwnerStates.main_menu)

    await call.message.edit_text(
        "👥 Xodimlar va talabalarni import qilish bo‘limi.\n\n"
        "Hozircha import funksiyasi '🏛 OTM va fakultetlar' bo‘limi orqali amalga oshiriladi.",
        reply_markup=get_back_inline_kb("owner_menu"),
    )
    await call.answer()


# -------------------------------------------------------------
#                 E'LONLAR VA BANNERLAR MENYUSI
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_ann_menu")
async def cb_owner_ann_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(call, session)
    if not staff:
        return

    await state.clear()
    
    await call.message.edit_text(
        "📢 <b>E'lonlar va Bannerlar bo'limi</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=get_owner_announcement_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "owner_ann_list")
async def cb_owner_ann_list(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(call, session)
    if not staff:
        return

    # Fetch active announcements
    result = await session.execute(
        select(Announcement)
        .where(Announcement.is_active == True)
        .order_by(Announcement.id.desc())
        .limit(20)
    )
    announcements = result.scalars().all()

    if not announcements:
        await call.message.edit_text(
            "ℹ️ Hozircha faol e'lonlar mavjud emas.",
            reply_markup=get_back_inline_kb("owner_ann_menu"),
            parse_mode="HTML"
        )
        await call.answer()
        return

    await call.message.edit_text(
        "📋 <b>Faol e'lonlar ro'yxati:</b>\n"
        "Batafsil ko'rish va o'chirish uchun tanlang:",
        reply_markup=get_active_announcements_kb(announcements),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("owner_ann_view:"))
async def cb_owner_ann_view(call: CallbackQuery, session: AsyncSession):
    ann_id = int(call.data.split(":")[1])
    ann = await session.get(Announcement, ann_id)
    
    if not ann:
        await call.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    text = (
        f"📝 <b>E'lon:</b> {ann.title}\n"
        f"📅 <b>Sana:</b> {ann.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{ann.content or ''}\n"
    )
    if ann.link:
        text += f"\n🔗 Link: {ann.link}"

    await call.message.edit_text(
        text,
        reply_markup=get_announcement_actions_kb(ann.id),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("owner_ann_del:"))
async def cb_owner_ann_delete(call: CallbackQuery, session: AsyncSession):
    ann_id = int(call.data.split(":")[1])
    ann = await session.get(Announcement, ann_id)
    
    if not ann:
        await call.answer("❌ E'lon topilmadi.", show_alert=True)
        return

    ann.is_active = False
    await session.commit()
    
    await call.answer("✅ E'lon o'chirildi!", show_alert=True)
    
    # Refresh list
    await cb_owner_ann_list(call, None, session)


# -------------------------------------------------------------
#                 BROADCAST (E‘LON YUBORISH)
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_broadcast")
async def cb_owner_broadcast(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    staff = await _ensure_owner(call, session)
    if not staff:
        return

    await state.set_state(OwnerStates.broadcasting_message)

    await call.message.edit_text(
        "📢 <b>Keng qamrovli xabar (Broadcast)</b>\n\n"
        "Barcha foydalanuvchilarga (talaba va xodimlarga) xabar yuboriladi.\n"
        "Matn, rasm, video yoki hujjat yuborishingiz mumkin.\n\n"
        "👇 Xabarni yuboring:",
        reply_markup=get_back_inline_kb("owner_ann_menu"),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(OwnerStates.broadcasting_message)
async def owner_process_broadcast(message: Message, state: FSMContext):
    
    # Xabarni nusxalash uchun message_id va chat_id saqlaymiz
    await state.update_data(
        broadcast_chat_id=message.chat.id,
        broadcast_message_id=message.message_id
    )
    
    # Tasdiqlash tugmasi
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yuborishni boshlash", callback_data="owner_broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="owner_menu")]
    ])

    await message.copy_to(chat_id=message.chat.id, reply_markup=kb)
    
    await message.answer(
        "👆 Yuqorida xabar ko'rinishi.\n"
        "Agar hammasi to'g'ri bo'lsa, <b>Yuborishni boshlash</b> tugmasini bosing.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "owner_broadcast_confirm")
async def cb_confirm_broadcast(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    chat_id = data.get("broadcast_chat_id")
    message_id = data.get("broadcast_message_id")
    
    if not chat_id or not message_id:
        await call.answer("Xatolik: Xabar topilmadi.", show_alert=True)
        return

    await call.message.edit_text("⏳ <b>Xabar yuborish boshlandi...</b>\n\nBu biroz vaqt olishi mumkin.", parse_mode="HTML")
    
    # Barcha foydalanuvchilar (TgAccount)
    try:
        accounts = await session.scalars(select(TgAccount))
        accounts = accounts.all()
    except Exception as e:
         logger.error(f"Error fetching accounts: {e}")
         await call.message.answer(f"Xatolik: {e}")
         return

    total = len(accounts)
    sent = 0
    blocked = 0
    errors = 0
    
    start_time = datetime.utcnow()
    
    for i, acc in enumerate(accounts):
        try:
            await call.bot.copy_message(
                chat_id=acc.telegram_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            sent += 1
        except Exception as e:
            # TelegramForbiddenError va boshqalar
            err_str = str(e).lower()
            if "blocked" in err_str or "chat not found" in err_str or "forbidden" in err_str:
                blocked += 1
            else:
                errors += 1
                logger.error(f"Broadcast error for {acc.telegram_id}: {e}")
        
        # Throttling to avoid 30 msg/sec limit
        # Har 20 ta xabarda biroz kutish
        if i % 20 == 0:
            await asyncio.sleep(0.5) 
            
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    report = (
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"👥 Umumiy: {total}\n"
        f"✅ Yuborildi: {sent}\n"
        f"🚫 Bloklagan: {blocked}\n"
        f"⚠️ Xatoliklar: {errors}\n\n"
        f"⏱ Vaqt: {duration:.1f} soniya"
    )
    
    await call.message.answer(report, reply_markup=get_back_inline_kb("owner_ann_menu"), parse_mode="HTML")
    await state.clear()
    await call.answer()


# -------------------------------------------------------------
#                   DEVELOPER MENYUSI
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_dev")
async def cb_owner_dev(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    """ Developerlar ro'yxatini ko'rsatish """
    staff = await _ensure_owner(call, session)
    if not staff:
        return

    # Faqat OWNER va DEVELOPER developer qo'sha/o'chira oladi
    is_privileged = (user_id == OWNER_TELEGRAM_ID or staff.role in [StaffRole.OWNER, StaffRole.DEVELOPER])

    # Developerlarni bazadan olamiz
    result = await session.execute(
        select(Staff).where(Staff.role == StaffRole.DEVELOPER, Staff.is_active == True)
    )
    developers = result.scalars().all()

    text = "👨‍💻 <b>Developerlar (Dasturchilar) ro'yxati</b>\n\n"
    if not developers:
        text += "Hozircha developerlar yo'q."
    else:
        for i, dev in enumerate(developers, 1):
            text += f"{i}. {dev.full_name} (ID: {dev.telegram_id})\n"

    await call.message.edit_text(
        text,
        reply_markup=get_owner_developers_kb(developers) if is_privileged else get_back_inline_kb("owner_menu"),
        parse_mode="HTML"
    )
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "owner_dev_add")
async def cb_owner_dev_add(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """ Developer qo'shishni boshlash """
    if call.from_user.id != OWNER_TELEGRAM_ID:
        return await call.answer("❌ Faqat asosiy Owner developer qo'sha oladi.", show_alert=True)

    await state.set_state(OwnerStates.waiting_dev_tg_id)
    await call.message.edit_text(
        "➕ <b>Yangi developer qo'shish</b>\n\n"
        "Iltimos, yangi developerning <b>Telegram ID</b> sini yuboring.\n"
        "Foydalanuvchi botdan ro'yxatdan o'tgan bo'lishi kerak.",
        parse_mode="HTML",
        reply_markup=get_dev_add_cancel_kb()
    )
    await call.answer()


@router.message(OwnerStates.waiting_dev_tg_id)
async def owner_add_dev_process(message: Message, state: FSMContext, session: AsyncSession):
    """ Telegram ID qabul qilib xodimni developer qilish """
    tg_id_str = message.text.strip()
    if not tg_id_str.isdigit():
        return await message.answer("❌ Telegram ID raqamlardan iborat bo'lishi kerak.")

    target_tg_id = int(tg_id_str)

    # 1. TgAccount dan foydalanuvchini qidiramiz
    result = await session.execute(
        select(TgAccount).where(TgAccount.telegram_id == target_tg_id)
    )
    acc = result.scalar_one_or_none()

    if not acc:
        return await message.answer(
            "❌ Bu foydalanuvchi botdan ro'yxatdan o'tmagan.\n"
            "Avval u botni ishga tushirishi kerak."
        )

    # 2. Staff jadvalida bormi yoki yangi yaratish kerakmi?
    if acc.staff_id:
        result = await session.execute(select(Staff).where(Staff.id == acc.staff_id))
        staff_member = result.scalar_one_or_none()
        if staff_member:
            staff_member.role = StaffRole.DEVELOPER
            staff_member.is_active = True
    else:
        # Yangi staff yaratamiz (Student bo'lsa ham developer qilaveramiz)
        # Student ma'lumotlariniStaff ga nusxalaymiz yoki shunchaki staff yaratamiz
        full_name = "Yangi Developer"
        if acc.student_id:
            student = await session.get(Student, acc.student_id)
            if student:
                full_name = student.full_name

        staff_member = Staff(
            full_name=full_name,
            jshshir=f"DEV_{target_tg_id}", # Dummy JSHSHIR
            role=StaffRole.DEVELOPER,
            telegram_id=target_tg_id,
            is_active=True
        )
        session.add(staff_member)
        await session.flush()
        acc.staff_id = staff_member.id

    await session.commit()

    # 3. Foydalanuvchiga xabar yuboramiz
    try:
        await message.bot.send_message(
            target_tg_id,
            "🎉 <b>Tabriklaymiz!</b>\n\n"
            "Siz TalabaHamkor botida <b>Developer</b> etib tayinlandingiz.\n"
            "Endi sizda barcha boshqaruv huquqlari mavjud.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify new developer {target_tg_id}: {e}")

    await message.answer(
        f"✅ Foydalanuvchi (ID: {target_tg_id}) muvaffaqiyatli developer etib tayinlandi.",
        reply_markup=get_back_inline_kb("owner_dev")
    )
    await state.clear()


@router.callback_query(F.data.startswith("owner_dev_del:"))
async def cb_owner_dev_delete(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    """ Developerni o'chirish """
    if call.from_user.id != OWNER_TELEGRAM_ID:
        return await call.answer("❌ Faqat asosiy Owner developerlarni o'chira oladi.", show_alert=True)

    dev_id = int(call.data.split(":")[1])
    dev = await session.get(Staff, dev_id)

    if not dev:
        return await call.answer("❌ Developer topilmadi.", show_alert=True)

    # Rolni 'tyutor' yoki shunchaki deactivated qilish (bizda tyutor default bo'lishi mumkin yoki xodimlikdan butunlay olib tashlash)
    # User talab bo'yicha 'o'chirish' degani uchun is_active=False qilamiz yoki rolni pasaytiramiz
    dev.is_active = False # Butunlay o'chiramiz staff sifatida
    await session.commit()

    await call.message.edit_text(
        f"🗑 Developer <b>{dev.full_name}</b> o'chirildi.",
        reply_markup=get_back_inline_kb("owner_dev"),
        parse_mode="HTML"
    )
    await call.answer()


# -------------------------------------------------------------
#                 BOT SOZLAMALARI MENYUSI
# -------------------------------------------------------------
@router.callback_query(F.data == "owner_settings")
async def cb_owner_settings(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):

    staff = await _ensure_owner(call, session)
    if not staff:
        return

    await call.message.edit_text(
        "⚙️ Bot umumiy sozlamalari.\n\n"
        "Keyingi bosqichda real sozlamalar bilan to‘ldiriladi.",
        reply_markup=get_back_inline_kb("owner_menu"),
    )
    await state.set_state(OwnerStates.main_menu)
    await call.answer()




# ============================================================
# 2) IMPORTNI BOSHLASH
# ============================================================
@router.callback_query(F.data.func(lambda d: d.startswith("uni_import_start:")))
async def cb_import_start(call: CallbackQuery, state: FSMContext):

    _, uni_id_str = call.data.split(":", 1)
    university_id = int(uni_id_str)

    # Bu bayroq 3 ta tugma chiqmasligi uchun kerak
    await state.update_data(
        university_id=university_id,
        import_faculties=[],
        import_staff=[],
        import_students=[],
        import_ready_shown=False
    )

    await state.set_state(OwnerStates.importing_csv_files)

    await call.message.edit_text(
        "📥 <b>CSV import boshlandi.</b>\n\n"
        "Ketma-ket 3 ta faylni yuboring:\n"
        "1️⃣ faculties.csv\n"
        "2️⃣ staff.csv\n"
        "3️⃣ students.csv",
        parse_mode="HTML",
        reply_markup=get_import_retry_kb(university_id)
    )
    await call.answer()


# ============================================================
# 3) CSV FAYL QABUL QILISH (YANGILANGAN — TYUTOR GURUHLARI BILAN)
# ============================================================
@router.message(OwnerStates.importing_csv_files, F.document)
async def owner_handle_import_files(message: Message, state: FSMContext):

    data = await state.get_data()
    university_id = data["university_id"]

    doc = message.document
    filename = doc.file_name.lower()

    upload_dir = Path("/var/www/talabahamkorbot/uploads/import")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_info = await message.bot.get_file(doc.file_id)
    local_path = upload_dir / filename
    await message.bot.download_file(file_info.file_path, destination=local_path)

    try:
        with open(local_path, "r", encoding="utf-8-sig") as f:
            raw = f.read()
    except Exception:
        return await message.answer("❌ CSV faylni o‘qib bo‘lmadi.")

    rows = list(csv.DictReader(StringIO(raw)))
    if not rows:
        return await message.answer("❌ CSV bo‘sh.")

    errors = []

    # ============================================================
    # 1) FAKULTETLAR
    # ============================================================
    if filename == "faculties.csv":
        facs = data.get("import_faculties", [])
        for i, r in enumerate(rows, start=2):
            code = (r.get("faculty_code") or "").strip()
            name = (r.get("faculty_name") or "").strip()

            if not code or not name:
                errors.append(f"{i}-qator: faculty_code va faculty_name majburiy.")
            else:
                facs.append({"faculty_code": code, "faculty_name": name})

        if errors:
            return await message.answer("\n".join(errors))

        await state.update_data(import_faculties=facs)
        return await message.answer("📘 faculties.csv qabul qilindi.")

    # ============================================================
    # 2) XODIMLAR (TYUTOR GURUHLARI BILAN)
    # ============================================================
    elif filename == "staff.csv":

        staff_list = data.get("import_staff", [])
        tutor_groups_map = data.get("tutor_groups_map", {})

        for i, r in enumerate(rows, start=2):
            jsh = (r.get("jshshir") or "").strip()
            full = (r.get("full_name") or "").strip()
            role = (r.get("role") or "").strip().lower()
            fac = (r.get("faculty_code") or "").strip()
            phone = (r.get("phone") or "").strip()
            position = (r.get("position") or "").strip()
            groups_raw = (r.get("tutor_groups") or "").strip()

            if not jshshir or not full or not role:
                errors.append(f"{i}-qator: jshshir, full_name, role majburiy.")
                continue

            # TYUTOR uchun faculty_code majburiy
            if role in ("dekanat", "tyutor") and not fac:
                errors.append(f"{i}-qator: '{role}' uchun faculty_code majburiy.")
                continue

            staff_list.append({
                "jshshir": jshshir,
                "full_name": full,
                "role": role,
                "faculty_code": fac or None,
                "phone": phone or None,
                "position": position or None,
            })

            # 🔥 TYUTOR GURUHLARI
            if role == "tyutor":
                if groups_raw:
                    group_list = [g.strip() for g in groups_raw.split(";") if g.strip()]
                    tutor_groups_map[jsh] = group_list
                else:
                    tutor_groups_map[jsh] = []

        if errors:
            return await message.answer("\n".join(errors))

        await state.update_data(import_staff=staff_list)
        await state.update_data(tutor_groups_map=tutor_groups_map)

        return await message.answer("🧑‍🏫 staff.csv qabul qilindi (tyutor guruhlari bilan).")

    # ============================================================
    # 3) TALABALAR
    # ============================================================
    elif filename == "students.csv":
        students = data.get("import_students", [])
        for i, r in enumerate(rows, start=2):
            hemis = (r.get("hemis_login") or "").strip()
            full = (r.get("full_name") or "").strip()
            group = (r.get("group_number") or "").strip()
            fac = (r.get("faculty_code") or "").strip()
            phone = (r.get("phone") or "").strip()

            if not hemis or not full or not group or not fac:
                errors.append(f"{i}-qator: barcha ustunlar majburiy (telefon ixtiyoriy).")
                continue

            students.append({
                "hemis_login": hemis,
                "full_name": full,
                "group_number": group,
                "faculty_code": fac,
                "phone": phone or None,
            })

        if errors:
            return await message.answer("\n".join(errors))

        await state.update_data(import_students=students)
        return await message.answer("🎓 students.csv qabul qilindi.")

    else:
        return await message.answer("❌ Noto‘g‘ri fayl nomi.")

    # ==========================================
    # 🔥 3 ta CSV qabul qilinganda faqat 1 marta tugma chiqadi
    # ==========================================
    data = await state.get_data()

    if (
        data.get("import_faculties")
        and data.get("import_staff")
        and data.get("import_students")
        and not data.get("import_ready_shown")
    ):
        await state.update_data(import_ready_shown=True)

        await message.answer(
            "✅ <b>3 ta CSV to‘liq qabul qilindi!</b>\n"
            "Importni tasdiqlang.",
            parse_mode="HTML",
            reply_markup=get_import_confirm_kb(university_id)
        )


# ============================================================
# 4) NO-MOS XABAR
# ============================================================
@router.message(OwnerStates.importing_csv_files, F.document.is_(None))
async def wrong_import_type(message: Message, state: FSMContext):

    data = await state.get_data()

    if (
        data.get("import_faculties")
        and data.get("import_staff")
        and data.get("import_students")
    ):
        return

    await message.answer(
        "ℹ️ Iltimos CSV fayllarni <b>hujjat</b> sifatida yuboring.",
        parse_mode="HTML"
    )


# ============================================================
# 5) IMPORTNI TASDIQLASH
# ============================================================
@router.callback_query(F.data.func(lambda d: d.startswith("uni_import_confirm:")))
async def cb_import_confirm(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    _, uni_id_str = call.data.split(":", 1)
    university_id = int(uni_id_str)

    data = await state.get_data()
    facs = data.get("import_faculties")
    staff_rows = data.get("import_staff")
    students = data.get("import_students")

    if not (facs and staff_rows and students):
        await call.message.answer("❌ 3 ta CSV hali to‘liq yuklanmagan.")
        await call.answer()
        return

    try:
        fac_code_to_id: dict[str, int] = {}

        # ======================================
        # 1) FAKULTETLAR — mavjud bo‘lsa SKIP
        # ======================================
        for f in facs:
            existing_faculty = await session.execute(
                select(Faculty).where(
                    Faculty.university_id == university_id,
                    Faculty.faculty_code == f["faculty_code"]
                )
            )
            existing_faculty = existing_faculty.scalar_one_or_none()

            if existing_faculty:
                logger.info(f"SKIP faculty: {f['faculty_code']} (already exists)")
                fac_code_to_id[f["faculty_code"]] = existing_faculty.id
                continue

            faculty = Faculty(
                university_id=university_id,
                faculty_code=f["faculty_code"],
                name=f["faculty_name"],
                is_active=True,
            )
            session.add(faculty)
            await session.flush()
            logger.info(f"ADD faculty: {f['faculty_code']}")
            fac_code_to_id[f["faculty_code"]] = faculty.id

        # ======================================
        # 2) STAFF — mavjud bo‘lsa SKIP
        # + Tyutor guruhlarini biriktirish
        # ======================================
        for row in staff_rows:
            role_enum = StaffRole(row["role"])

            faculty_id = (
                fac_code_to_id.get(row["faculty_code"])
                if role_enum in (StaffRole.DEKANAT, StaffRole.TYUTOR)
                else None
            )

            # Staff mavjudligini tekshirish
            existing_staff = await session.execute(
                select(Staff).where(
                    Staff.jshshir == row["jshshir"],
                    Staff.university_id == university_id
                )
            )
            existing_staff = existing_staff.scalar_one_or_none()

            if existing_staff:
                logger.info(f"SKIP staff: {row['full_name']} (jshshir exists)")

                # Agar tyutor bo‘lsa, guruhlarini ham tekshirib qo‘shib yuborish kerak
                if role_enum == StaffRole.TYUTOR:
                    groups_raw = row.get("groups", "")
                    if groups_raw:
                        group_list = [g.strip() for g in groups_raw.split(",") if g.strip()]

                        for grp in group_list:
                            tg = TutorGroup(
                                tutor_id=existing_staff.id,
                                group_number=grp
                            )
                            try:
                                session.add(tg)
                                await session.flush()
                            except Exception:
                                await session.rollback()
                                continue

                continue

            # Staff yangi bo‘lsa — yaratiladi
            staff = Staff(
                full_name=row["full_name"],
                jshshir=row["jshshir"],
                role=role_enum,
                phone=row.get("phone"),
                position=row.get("position"),
                university_id=university_id,
                faculty_id=faculty_id,
                is_active=True,
            )
            session.add(staff)
            await session.flush()  # staff.id olish uchun

            logger.info(f"ADD staff: {row['full_name']} ({row['jshshir']})")

            # TYUTOR bo‘lsa, guruhlar biriktiriladi
            if role_enum == StaffRole.TYUTOR:
                groups_raw = row.get("groups", "")
                if groups_raw:
                    group_list = [g.strip() for g in groups_raw.split(",") if g.strip()]

                    for grp in group_list:
                        tg = TutorGroup(
                            tutor_id=staff.id,
                            group_number=grp
                        )
                        try:
                            session.add(tg)
                            await session.flush()
                        except Exception:
                            await session.rollback()
                            continue

        # ======================================
        # 3) TALABALAR — mavjud bo‘lsa SKIP
        # ======================================
        for row in students:
            faculty_id = fac_code_to_id.get(row["faculty_code"])

            existing_student = await session.execute(
                select(Student).where(
                    Student.hemis_login == row["hemis_login"],
                    Student.university_id == university_id
                )
            )
            existing_student = existing_student.scalar_one_or_none()

            if existing_student:
                logger.info(f"SKIP student: {row['full_name']} (hemis exists)")
                continue

            student = Student(
                full_name=row["full_name"],
                hemis_login=row["hemis_login"],
                group_number=row["group_number"],
                phone=row.get("phone"),
                university_id=university_id,
                faculty_id=faculty_id,
                is_active=True,
            )
            logger.info(f"ADD student: {row['full_name']} ({row['hemis_login']})")
            session.add(student)

        # ======================================
        # COMMIT
        # ======================================
        await session.commit()

        await state.set_state(OwnerStates.university_selected)

        await call.message.edit_text(
            "✅ Import muvaffaqiyatli yakunlandi.",
            reply_markup=get_university_actions_kb(university_id),
        )
        await call.answer()

    except Exception as e:
        await session.rollback()
        logger.exception("Import xatosi: %s", e)
        await call.message.answer("❌ Importda ichki xatolik yuz berdi. Loglarni tekshiring.")
        await call.answer()

# ============================================================
#  📥 SHABLON CSV FAYLLARNI YUKLAB OLISH HANDLER
# ============================================================
from aiogram.types import BufferedInputFile
from pathlib import Path

@router.callback_query(F.data.startswith("download_csv_templates:"))
async def cb_download_csv_templates(call: CallbackQuery):
    _, uni_id = call.data.split(":", 1)

    # Shablonlar zip fayli
    template_path = Path("/var/www/talabahamkorbot/uploads/templates.zip")

    if not template_path.exists():
        return await call.message.answer("❌ Shablon fayllar topilmadi.")

    try:
        await call.message.answer_document(
            document=BufferedInputFile.from_file(template_path),
            caption="📄 CSV shablonlar to‘plami"
        )
        await call.answer()
    except Exception as e:
        await call.message.answer("❌ Faylni yuborishda xatolik yuz berdi.")
        print("DOWNLOAD ERROR:", e)


from aiogram.types import FSInputFile

@router.callback_query(F.data.startswith("download_csv_templates"))
async def download_csv_templates(call: CallbackQuery):
    path = "/var/www/talabahamkorbot/uploads/templates.zip"

    try:
        file = FSInputFile(path, filename="templates.zip")
        await call.message.answer_document(
            document=file,
            caption="📥 CSV shablonlar to‘plami"
        )
        await call.answer()
    except Exception as e:
        await call.message.answer(f"❌ Faylni yuborib bo‘lmadi:\n{e}")
        await call.answer()

@router.callback_query(F.data == "owner_add_university")
async def owner_add_university(call: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerStates.entering_uni_name)
    await call.message.edit_text("🏫 Yangi universitet nomini kiriting:")
    await call.answer()

@router.message(OwnerStates.entering_uni_name)
async def owner_add_uni_name(message: Message, state: FSMContext):
    await state.update_data(university_name=message.text.strip())
    await state.set_state(OwnerStates.entering_short_name)
    await message.answer("✍️ Universitetning qisqa nomini kiriting (masalan: O‘zJOKU):")

@router.message(OwnerStates.entering_short_name)
async def owner_add_uni_short(message: Message, state: FSMContext):
    await state.update_data(short_name=message.text.strip())
    await state.set_state(OwnerStates.entering_new_uni_code)
    await message.answer("🔑 Universitet uchun noyob kod kiriting (masalan: OZJOKU):")

from sqlalchemy import select
from database.models import University

@router.message(OwnerStates.entering_new_uni_code)
async def owner_add_uni_code(message: Message, state: FSMContext, session: AsyncSession):

    code = message.text.strip().upper()
    data = await state.get_data()

    # Kod takrorlanmasligi kerak
    exists = await session.scalar(select(University).where(University.uni_code == code))
    if exists:
        return await message.answer("❌ Bu kod allaqachon mavjud. Boshqa kod kiriting.")

    uni = University(
        name=data["university_name"],
        short_name=data["short_name"],
        uni_code=code,
        is_active=True
    )
    session.add(uni)
    await session.commit()

    await state.clear()
    
    await message.answer(
        f"✅ <b>{uni.name}</b> muvaffaqiyatli qo‘shildi!",
        reply_markup=get_university_actions_kb(uni.id),
        parse_mode="HTML"
    )




# -------------------------------------------------------------
#                 BANNER SOZLAMALARI
# -------------------------------------------------------------
# -------------------------------------------------------------
#                 BANNER SOZLAMALARI (YANGILANGAN)
# -------------------------------------------------------------

@router.callback_query(F.data == "owner_banner_menu")
async def cb_owner_banner_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(call, session)
    if not staff: return

    await state.clear()
    
    await call.message.edit_text(
        "🖼 <b>Bannerlar boshqaruvi</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=get_owner_banner_menu_kb(),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "owner_banner_list")
async def cb_owner_banner_list(call: CallbackQuery, session: AsyncSession):
    # Fetch all banners
    result = await session.execute(select(Banner).order_by(Banner.id.desc()).limit(20))
    banners = result.scalars().all()
    
    if not banners:
        await call.answer("ℹ️ Bannerlar topilmadi.", show_alert=True)
        return

    await call.message.edit_text(
        "📋 <b>Bannerlar ro'yxati:</b>\n"
        "Batafsil ko'rish va boshqarish uchun tanlang:",
        reply_markup=get_banner_list_kb(banners),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("owner_banner_view:"))
async def cb_owner_banner_view(call: CallbackQuery, session: AsyncSession):
    banner_id = int(call.data.split(":")[1])
    banner = await session.get(Banner, banner_id)
    
    if not banner:
        await call.answer("❌ Banner topilmadi.", show_alert=True)
        return

    status_text = "✅ Faol" if banner.is_active else "⏹ Nofaol"
    text = (
        f"🖼 <b>Banner #{banner.id}</b>\n"
        f"Status: {status_text}\n"
        f"Yaratilgan: {banner.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"👁 Ko'rishlar: {banner.views}\n"
        f"👆 Link bosishlar: {banner.clicks}\n"
    )
    if banner.link:
        text += f"🔗 Link: {banner.link}\n"
        
    try:
        await call.message.answer_photo(
            photo=banner.image_file_id,
            caption=text,
            reply_markup=get_banner_actions_kb(banner.id, banner.is_active),
            parse_mode="HTML"
        )
        # Delete old menu message to avoid clutter, or keeping it is fine. 
        # Typically better to edit, but can't edit text to photo.
        await call.message.delete() 
    except Exception as e:
        await call.message.answer(f"Rasm yuklashda xatolik: {e}\n\n{text}")

    await call.answer()


@router.callback_query(F.data.startswith("owner_banner_toggle:"))
async def cb_owner_banner_toggle(call: CallbackQuery, session: AsyncSession):
    banner_id = int(call.data.split(":")[1])
    banner = await session.get(Banner, banner_id)
    
    if not banner:
        return await call.answer("❌ Banner topilmadi.", show_alert=True)
        
    if banner.is_active:
        # Deactivate
        banner.is_active = False
        await session.commit()
        await call.answer("⏹ Banner nofaol qilindi.")
    else:
        # Activate (and deactivate others)
        from sqlalchemy import update
        await session.execute(update(Banner).where(Banner.is_active == True).values(is_active=False))
        banner.is_active = True
        await session.commit()
        await call.answer("✅ Banner faollashtirildi!")
        
    # Refresh view
    # since we can't easily edit the photo caption and markup perfectly without resending in some clients,
    # let's try editing caption.
    status_text = "✅ Faol" if banner.is_active else "⏹ Nofaol"
    text = (
        f"🖼 <b>Banner #{banner.id}</b>\n"
        f"Status: {status_text}\n"
        f"Yaratilgan: {banner.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"👁 Ko'rishlar: {banner.views}\n"
        f"👆 Link bosishlar: {banner.clicks}\n"
    )
    if banner.link:
        text += f"🔗 Link: {banner.link}\n"
        
    try:
        await call.message.edit_caption(
            caption=text,
            reply_markup=get_banner_actions_kb(banner.id, banner.is_active),
            parse_mode="HTML"
        )
    except:
        # Reset view if edit fails
        await cb_owner_banner_list(call, session)


@router.callback_query(F.data.startswith("owner_banner_del:"))
async def cb_owner_banner_delete(call: CallbackQuery, session: AsyncSession):
    banner_id = int(call.data.split(":")[1])
    banner = await session.get(Banner, banner_id)
    
    if not banner:
        return await call.answer("❌ Banner topilmadi.", show_alert=True)
        
    await session.delete(banner)
    await session.commit()
    
    await call.answer("🗑 Banner o'chirildi!", show_alert=True)
    
    # Try to delete the photo message and show list
    try:
        await call.message.delete()
    except:
        pass
        
    await cb_owner_banner_list(call, session)


@router.callback_query(F.data == "owner_banner_add")
async def cb_owner_banner_add(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(call, session)
    if not staff:
        return

    await state.set_state(OwnerStates.waiting_banner_image)
    await call.message.edit_text(
        "🖼 <b>Banner Sozlash</b>\n\n"
        "Ilovadagi bosh sahifa bannerini o'zgartirish.\n"
        "Iltimos, banner uchun <b>rasm (photo)</b> yuboring.\n"
        "O'lcham: 16:9 yoki shunga yaqin bo'lishi tavsiya etiladi.",
        reply_markup=get_back_inline_kb("owner_banner_menu"),
        parse_mode="HTML"
    )
    await call.answer()

@router.message(OwnerStates.waiting_banner_image)
async def owner_process_banner_image(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(f"⚠️ Rasm yuborilmadi. Kelgan xabar turi: {message.content_type}\nIltimos, rasm (photo) yuboring.")
        return

    # Eng katta rasmni olamiz
    photo = message.photo[-1]
    file_id = photo.file_id
    
    await state.update_data(banner_file_id=file_id)
    await state.set_state(OwnerStates.waiting_banner_link)
    
    await message.answer(
        "✅ Rasm qabul qilindi.\n\n"
        "Endi banner bosilganda ochiladigan <b>havola (link)</b>ni yuboring.\n"
        "Agar havola kerak bo'lmasa, '0' yoki 'yoq' deb yozing.",
        reply_markup=get_back_inline_kb("owner_banner_menu")
    )

@router.message(OwnerStates.waiting_banner_link)
async def owner_process_banner_link(message: Message, state: FSMContext, session: AsyncSession):
    link_text = message.text.strip()
    
    data = await state.get_data()
    file_id = data.get("banner_file_id")
    
    final_link = None
    if link_text.lower() not in ['0', 'yoq', 'yo\'q', 'no', 'none']:
        if not link_text.startswith("http"):
             # Agar http bo'lmasa, qo'shib qo'yamiz yoki shunday qoldiramiz (client handle qiladi)
             pass
        final_link = link_text
        
    # Oldingi bannerlarni nofaol qilish
    await session.execute(
        select(Banner).where(Banner.is_active == True)
    )
    # Update logic is tricky with select, better to update directly
    # Or just set all to False
    from sqlalchemy import update
    await session.execute(update(Banner).where(Banner.is_active == True).values(is_active=False))
    
    # Yangi bannerni saqlash
    new_banner = Banner(
        image_file_id=file_id,
        link=final_link,
        is_active=True
    )
    session.add(new_banner)
    await session.commit()
    
    await message.answer(
        "✅ <b>Banner muvaffaqiyatli o'rnatildi!</b>\n\n"
        "Endi ilovada yangi banner ko'rinadi.",
        reply_markup=get_back_inline_kb("owner_banner_menu"),
        parse_mode="HTML"
    )
    await state.clear()


# =============================================================
#  📌 REPLY KEYBOARD HANDLERS (TEXT COMMANDS)
# =============================================================

@router.message(F.text == "🏛 OTM va fakultetlar")
async def msg_owner_universities(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    staff = await _ensure_owner(message, session)
    if not staff: return

    result = await session.execute(select(University).order_by(University.id))
    universities = result.scalars().all()

    if not universities:
        await message.answer(
            "🏛 OTMlar ro'yxati bo'sh.\n\n"
            "Yangi OTM qo'shish uchun <b>uni_code</b> kiriting.",
            parse_mode="HTML",
            reply_markup=get_back_inline_kb("owner_menu")
        )
        await state.set_state(OwnerStates.entering_uni_code)
        return

    text = "🏛 <b>Mavjud universitetlar:</b>\n\n"
    for i, uni in enumerate(universities, 1):
        text += f"{i}. {uni.name} (<code>{uni.uni_code}</code>)\n"

    text += "\nSozlash uchun raqamlardan birini tanlang:"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_numbered_universities_kb(universities)
    )

@router.message(F.text == "👥 Xodim / talaba importi")
async def msg_owner_import(message: Message, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(message, session)
    if not staff: return

    await state.set_state(OwnerStates.main_menu)
    await message.answer(
        "👥 Xodimlar va talabalarni import qilish bo‘limi.\n\n"
        "Hozircha import funksiyasi '🏛 OTM va fakultetlar' bo‘limi orqali amalga oshiriladi.",
        reply_markup=get_back_inline_kb("owner_menu"),
    )

@router.message(F.text == "📢 Umumiy e'lon yuborish")
async def msg_owner_broadcast(message: Message, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(message, session)
    if not staff: return

    # User requested to open the Announcement Menu instead of direct broadcast
    await state.clear()
    
    await message.answer(
        "📢 <b>E'lonlar va Bannerlar bo'limi</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=get_owner_announcement_menu_kb(),
        parse_mode="HTML"
    )

@router.message(F.text == "👨‍💻 Developerlar boshqaruvi")
async def msg_owner_dev(message: Message, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(message, session)
    if not staff: return

    user_id = message.from_user.id
    # Check privileges
    is_privileged = (user_id == OWNER_TELEGRAM_ID or staff.role in [StaffRole.OWNER, StaffRole.DEVELOPER])

    result = await session.execute(
        select(Staff).where(Staff.role == StaffRole.DEVELOPER, Staff.is_active == True)
    )
    developers = result.scalars().all()

    text = "👨‍💻 <b>Developerlar (Dasturchilar) ro'yxati</b>\n\n"
    if not developers:
        text += "Hozircha developerlar yo'q."
    else:
        for i, dev in enumerate(developers, 1):
            text += f"{i}. {dev.full_name} (ID: {dev.telegram_id})\n"

    await message.answer(
        text,
        reply_markup=get_owner_developers_kb(developers) if is_privileged else get_back_inline_kb("owner_menu"),
        parse_mode="HTML"
    )
    await state.clear()

@router.message(F.text == "⚙️ Bot sozlamalari")
async def msg_owner_settings(message: Message, state: FSMContext, session: AsyncSession):
    staff = await _ensure_owner(message, session)
    if not staff: return

    await message.answer(
        "⚙️ Bot umumiy sozlamalari.\n\n"
        "Keyingi bosqichda real sozlamalar bilan to‘ldiriladi.",
        reply_markup=get_back_inline_kb("owner_menu"),
    )
    await state.set_state(OwnerStates.main_menu)


@router.message(F.text == "🏠 Bosh menyu")
async def msg_owner_main_menu(message: Message, state: FSMContext, session: AsyncSession):
    await state.set_state(OwnerStates.main_menu)
    text = await get_owner_dashboard_text(session)
    # We send Inline Keyboard to transition user to the new standard, 
    # but since they clicked a Reply button, they might be confused.
    # Ideally we should send the Reply Keyboard again if we want to support it fully.
    # But for now, let's just make it work.
    await message.answer(
        text,
        reply_markup=get_owner_main_menu_inline_kb(),
        parse_mode="HTML"
    )

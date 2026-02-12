from datetime import datetime
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import re

from database.models import (
    Student, TgAccount,
    UserActivity, UserActivityImage
)
from keyboards.inline_kb import (
    get_student_main_menu_kb,
    get_student_activities_kb,
    get_student_activities_detail_kb,
    get_student_activities_detail_kb,
    get_student_activities_detail_kb,
    get_activity_add_kb,
    get_student_kitobxonlik_menu_kb,
    get_date_select_inline_kb,
)
from keyboards.reply_kb import get_student_activity_reply_kb, get_date_select_kb
from aiogram.types import ReplyKeyboardRemove
from models.states import ActivityAddStates
from utils.student_utils import get_student_by_tg, check_premium_access

router = Router()

CATEGORIES = ["togarak", "yutuqlar", "marifat", "volontyorlik", "madaniy", "sport", "boshqa"]
MAX_IMAGES = 5


# ============================================================
# HELPERS
# ============================================================

async def _get_student_by_tg_local(telegram_id: int, session: AsyncSession):
    # This matches the signature used in this file but routes through the centralized utility
    return await get_student_by_tg(telegram_id, session)


# ============================================================
# 📊 FAOLLIKLAR STATISTIKASI
# ============================================================

@router.callback_query(F.data.in_({"student_activities", "student_activities:profile"}))
async def student_activities(call: CallbackQuery, session: AsyncSession, state: FSMContext):

    allowed, text, _ = await check_premium_access(call.from_user.id, session, "Ijtimoiy Faollik")
    if not allowed:
        return await call.answer(text, show_alert=True)

    student = await get_student_by_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Talaba topilmadi!", show_alert=True)

    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"

    try:
        # Fetch all activities for this student
        # We only need category and status
        result = await session.execute(
            select(UserActivity.category, UserActivity.status)
            .where(UserActivity.student_id == student.id)
        )
        rows = result.all() # list of (category, status)

        # Initialize counters
        # Structure: { "volontyorlik": {"approved": 0, "pending": 0, "rejected": 0}, ... }
        stats = {cat: {"approved": 0, "pending": 0, "rejected": 0} for cat in CATEGORIES}
        total_counts = {"approved": 0, "pending": 0, "rejected": 0}

        for r_cat, r_status in rows:
            # Check if category is known (in case of old data or removed cats)
            if r_cat in stats:
                if r_status in stats[r_cat]:
                    stats[r_cat][r_status] += 1
                    total_counts[r_status] += 1
            else:
                # 'boshqa' or handle unexpected
                if "boshqa" in stats:
                    if r_status in stats["boshqa"]:
                        stats["boshqa"][r_status] += 1
                        total_counts[r_status] += 1

        # Text generation
        # Text generation
        text = "📊 <b>Faolliklar statistikasi</b>\n\n"
        
        # Descriptions mapping
        descriptions = {
            "togarak": "“5 muhim tashabbus” doirasidagi toʻgaraklarda faol ishtiroki",
            "yutuqlar": "Xalqaro, respublika, viloyat miqyosidagi koʻrik-tanlov, fan olimpiadalari va sport musobaqalarida erishgan natijalari",
            "marifat": "Talabalarning “Maʼrifat darslari”dagi faol ishtiroki",
            "volontyorlik": "Volontyorlik va jamoat ishlaridagi faolligi",
            "madaniy": "Teatr va muzey, xiyobon, kino, tarixiy qadamjolarga tashriflar",
            "sport": "Talabalarning sport bilan shugʻullanishi va sogʻlom turmush tarziga amal qilishi",
            "boshqa": "Boshqa turdagi faolliklar"
        }

        for cat in CATEGORIES:
            s_stats = stats[cat]
            desc = descriptions.get(cat, "")
            
            cat_name = cat.capitalize()
            if cat == "yutuqlar": cat_name = "Yutuqlar"
            elif cat == "volontyorlik": cat_name = "Volontyorlik"
            elif cat == "marifat": cat_name = "Ma'rifat darslari"
            elif cat == "sport": cat_name = "Sport"
            elif cat == "togarak": cat_name = "To'garak"
            elif cat == "madaniy": cat_name = "Madaniy tashriflar"
            elif cat == "boshqa": cat_name = "Boshqa"

            # Format: **Name** (*Description*)
            #         ✔️ X | ⏳ Y | ✖️ Z
            text += f"<b>{cat_name}</b> <i>({desc})</i>\n"
            text += f"✔️ {s_stats['approved']} | ⏳ {s_stats['pending']} | ✖️ {s_stats['rejected']}\n\n"

        # 2. Total Summary
        text += (
            "➖➖➖➖➖➖➖➖➖➖\n"
            f"<b>Jami:</b> ✔️ {total_counts['approved']} | ⏳ {total_counts['pending']} | ✖️ {total_counts['rejected']}"
        )

    except Exception as e:
        return await call.answer(f"Stats error: {e}", show_alert=True)

    # Delete previous message to "refresh" info and add Reply Keyboard
    try:
        await call.message.delete()
    except Exception:
        pass

    try:
        # Remove Reply Keyboard if present from previous interactions
        temp_rm = await call.message.answer("...", reply_markup=ReplyKeyboardRemove())
        await temp_rm.delete()

        msg = await call.message.answer(
            f"{text}\n\n"
            " Quyidagilardan birini tanlang va pastdagi tugmani ishlating:",
            reply_markup=get_student_activities_kb(back_callback=back_to), # Inline (Batafsil, Kitobxonlik, Ortga)
            parse_mode="HTML"
        )
        
        await state.update_data(
            dashboard_msg_id=msg.message_id
        )
    except Exception as e:
        await call.answer(f"Send error: {e}", show_alert=True)
        return
    await call.answer()


# ============================================================
# 📋 BATAFSIL FAOLLIKLAR RO‘YXATI
# ============================================================

@router.callback_query(F.data == "student_activities_detail")
async def student_activities_detail(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    allowed, text, _ = await check_premium_access(call.from_user.id, session, "Ijtimoiy Faollik")
    if not allowed:
        return await call.answer(text, show_alert=True)

    # Delete instruction message if exists
    data = await state.get_data()
    instr_id = data.get("reply_instruction_msg_id")
    if instr_id:
        try:
            await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=instr_id)
        except:
            pass


    student = await get_student_by_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Talaba topilmadi!", show_alert=True)

    acts = await session.scalars(
        select(UserActivity)
        .where(UserActivity.student_id == student.id)
        .order_by(UserActivity.id.desc())
    )
    acts = acts.all()

    if not acts:
        return await call.answer("Faolliklar mavjud emas!", show_alert=True)

    text = "" # Changed from "<b>📋 Barcha faolliklar</b>\n"
    total_count = len(acts) # Added this line

    for i, a in enumerate(acts, start=1):
        # Satus mapping
        status_map = {
            "approved": "Qabul qilingan",
            "pending": "Kutiliyapti",
            "rejected": "Rad etilgan"
        }
        status_text = status_map.get(a.status, a.status)

        text += (
            f"\n<b>{i}) {a.category.capitalize()}</b>\n"
            f"🏷 Nomi: <b>{a.name}</b>\n"
            f"📝 Tavsif: {a.description}\n"
            f"📅 Sana: <code>{a.date}</code>\n"
            f"📌 Holati: <b>{status_text}</b>\n"
        )


    try:
        await call.message.edit_text(
            f"📋 <b>Sizning faolliklaringiz ({total_count} ta):</b>\n\n{text}",
            reply_markup=get_student_activities_detail_kb(),
            parse_mode="HTML"
        )
    except Exception:
        pass
    await call.answer()


# ============================================================
# 🖼 BARCHA RASMLARNI KO‘RISH (YANGI FORMAT — MEDIA GROUP)
# ============================================================

from aiogram.types import InputMediaPhoto

@router.callback_query(F.data == "student_activities_images")
async def student_activities_images(call: CallbackQuery, session: AsyncSession, state: FSMContext):

    allowed, text, _ = await check_premium_access(call.from_user.id, session, "Ijtimoiy Faollik")
    if not allowed:
        return await call.answer(text, show_alert=True)

    student = await get_student_by_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Talaba topilmadi!", show_alert=True)

    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"

    acts = await session.scalars(
        select(UserActivity)
        .where(UserActivity.student_id == student.id)
        .order_by(UserActivity.id)
    )
    acts = acts.all()

    if not acts:
        return await call.answer("Faolliklar mavjud emas!", show_alert=True)

    await call.answer()

    for index, act in enumerate(acts):

        imgs = await session.scalars(
            select(UserActivityImage)
            .where(UserActivityImage.activity_id == act.id)
        )
        imgs = imgs.all()

        if not imgs:
            continue

        # Satus mapping
        status_map = {
            "approved": "Qabul qilingan",
            "pending": "Kutiliyapti",
            "rejected": "Rad etilgan"
        }
        status_text = status_map.get(act.status, act.status)

        caption = (
            f"<b>{act.category.capitalize()}</b>\n"
            f"Nomi: <b>{act.name}</b>\n"
            f"Tavsif: {act.description or '—'}\n"
            f"Sana: <code>{act.date or '—'}</code>\n"
            f"Holati: <b>{status_text}</b>"
        )

        
        if len(imgs) == 1:
            await call.message.answer_photo(
                imgs[0].file_id,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            # 2) Ko‘p rasm bo‘lsa — MEDIA GROUP
            media = []

            for i, img in enumerate(imgs):
                if i == 0:
                    media.append(InputMediaPhoto(media=img.file_id, caption=caption, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=img.file_id))

            await call.message.answer_media_group(media)
            
    # Oxirida menyuga qaytish
    await call.message.answer(
        "⬅️ Orqaga qaytish",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_activities_detail")]
            ]
        )
    )



# ============================================================
# ➕ FAOLLIK QO‘SHISH BOSHLANISHI
# ============================================================

# ============================================================
# ➕ FAOLLIK QO‘SHISH BOSHLANISHI (Reply Button or Inline)
# ============================================================

@router.message(F.text == "➕ Faollik qo‘shish")
async def student_add_activity_menu_reply(message: Message, session: AsyncSession, state: FSMContext):
    allowed, text, _ = await check_premium_access(message.from_user.id, session, "Faollik qo'shish")
    if not allowed:
         return await message.answer("⚠️ Faollik qo'shish uchun Premium obuna talab etiladi.")

    student = await get_student_by_tg(message.from_user.id, session)
    if not student:
         # Optionally handle non-student (e.g. Owner) nicely, but they passed premium check so just return or allow?
         # But usually activities require student relationship.
         return await message.answer("❌ Tizimda talaba sifatida aniqlanmadingiz.")
         
    # 1) Delete user's message to keep chat clean
    try:
        await message.delete()
    except Exception:
        pass

    # 2) Get saved dashboard message ID
    data = await state.get_data()
    dashboard_msg_id = data.get("dashboard_msg_id")

    # Remove Reply Keyboard immediately
    try:
        temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except:
        pass

    # Delete instruction message if exists (since user already pressed the button)
    instr_id = data.get("reply_instruction_msg_id")
    if instr_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=instr_id)
        except:
            pass


    if dashboard_msg_id:
        try:
            # 3) Edit the dashboard message
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=dashboard_msg_id,
                text="Qaysi kategoriyaga faollik qo‘shmoqchisiz?",
                reply_markup=get_activity_add_kb()
            )
        except Exception:
            # If editing fails (e.g. message too old), fall back to sending new message
            await message.answer(
                "Qaysi kategoriyaga faollik qo‘shmoqchisiz?",
                reply_markup=get_activity_add_kb()
            )
    else:
        # If no saved ID, just send new message
        await message.answer(
            "Qaysi kategoriyaga faollik qo‘shmoqchisiz?",
            reply_markup=get_activity_add_kb()
        )

@router.callback_query(F.data == "student_activity_add")
async def student_add_activity_menu_inline(call: CallbackQuery, session: AsyncSession):
    allowed, text, _ = await check_premium_access(call.from_user.id, session, "Faollik qo'shish")
    if not allowed:
        return await call.answer(text, show_alert=True)

    student = await get_student_by_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Talaba aniqlanmadi", show_alert=True)

    await call.message.edit_text(
        "Qaysi kategoriyaga faollik qo‘shmoqchisiz?",
        reply_markup=get_activity_add_kb()
    )
    await call.answer()


# ============================================================
# KITOBXONLIK MADANIYATI (MENU & INFO)
# ============================================================

# ============================================================

@router.callback_query(F.data == "student_kitobxonlik_menu")
async def kitobxonlik_menu(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    allowed, text, _ = await check_premium_access(call.from_user.id, session, "Kitobxonlik")
    if not allowed:
        return await call.answer(text, show_alert=True)

    student = await get_student_by_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Talaba aniqlanmadi", show_alert=True)
        
    # Remove Reply Keyboard if exists
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


    await call.message.edit_text(
        "📚 <b>Kitobxonlik madaniyati</b>\n\n"
        "Ushbu test <b>Grant taqsimoti</b> uchun baholash reglamentlaridan biri hisoblanadi.\n"
        "Sizning kitobxonlik darajangizni aniqlash orqali munosib nomzodlar saralab olinadi.\n\n"
        "Testni boshlash uchun quyidagi tugmani bosing:",
        reply_markup=get_student_kitobxonlik_menu_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "student_kitobxonlik_test")
async def kitobxonlik_info(call: CallbackQuery):
    await call.answer(
        "Kitobxonlik madaniyatini baholash uchun test e'lon qilinsa joylanadi",
        show_alert=True
    )

@router.callback_query(F.data == "student_kitobxonlik_books")
async def kitobxonlik_books(call: CallbackQuery):
    # Back button to Kitobxonlik menu
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_kitobxonlik_menu")]
    ])
    
    await call.message.edit_text(
        "📚 <b>Kitoblar ro'yixati</b>\n\n"
        "Grant taqsimoti uchun kitoblar ro'yixati hozircha taqdim etilmadi, taqdim etilishi bilan ro'yixat yangilanadi.",
        parse_mode="HTML",
        reply_markup=kb
    )


# ============================================================
# 1) KATEGORIYA
# ============================================================

@router.callback_query(F.data.in_([
    "act_add_vol", "act_add_marifat", "act_add_madaniy", "act_add_yutuq", "act_add_togarak", "act_add_sport", "act_add_boshqa"
]))
async def add_category(call: CallbackQuery, state: FSMContext):

    mapping = {
        "act_add_vol": "volontyorlik",
        "act_add_marifat": "marifat",
        "act_add_madaniy": "madaniy",
        "act_add_yutuq": "yutuqlar",
        "act_add_togarak": "togarak",
        "act_add_sport": "sport",
        "act_add_boshqa": "boshqa",
    }

    cat_val = mapping[call.data]

    await state.update_data(category=cat_val)
    await state.set_state(ActivityAddStates.NAME)

    try:
        # Custom prompt for 'togarak'
        if cat_val == "togarak":
            await call.message.edit_text("📝 To'garak nomini kiriting:")
        elif cat_val == "yutuqlar":
            await call.message.edit_text("📝 Yutuq nomini kiriting:")
        elif cat_val == "marifat":
            await call.message.edit_text("📝 Ma'rifat darsi mavzusini kiriting:")
        elif cat_val == "volontyorlik":
            await call.message.edit_text("📝 Volontyorlik nomini kiriting:")
        elif cat_val == "madaniy":
            await call.message.edit_text("📝 Madaniy tashrif nomini kiriting:")
        elif cat_val == "sport":
            await call.message.edit_text("📝 Faollik nomini kiriting:")
        else:
            await call.message.edit_text("📝 Faollik nomini kiriting:")
    except Exception:
        pass
    await call.answer()


# ============================================================
# 2) NOM
# ============================================================

@router.message(ActivityAddStates.NAME)
async def add_name(message: Message, state: FSMContext):

    await state.update_data(name=message.text)
    await state.set_state(ActivityAddStates.DESCRIPTION)
    
    data = await state.get_data()
    cat_val = data.get("category")

    if cat_val == "togarak":
         await message.answer("✏️ To'garak tasnifini kiriting:")
    elif cat_val == "yutuqlar":
         await message.answer("✏️ Yutuq tasnifini kiriting:")
    elif cat_val == "marifat":
         # User request: "Ma'rifat darsi tavsfini kiriting" (fixing typo to tavsifini)
         await message.answer("✏️ Ma'rifat darsi tavsifini kiriting:")
    elif cat_val == "volontyorlik":
         await message.answer("✏️ Volontyorlik tavsifini kiriting:")
    elif cat_val == "madaniy":
         await message.answer("✏️ Tashrif tavsifini kiriting:")
    elif cat_val == "sport":
         await message.answer("✏️ Faollik tavsifini kiriting:")
    elif cat_val == "boshqa":
         await message.answer("✏️ Faollik tavsifini kiriting:")
    else:
         await message.answer("✏️ Tavsifni kiriting:")


# ============================================================
# 3) TAVSIF
# ============================================================

@router.message(ActivityAddStates.DESCRIPTION)
async def add_description(message: Message, state: FSMContext):

    await state.update_data(description=message.text)
    await state.set_state(ActivityAddStates.DATE)

    await message.answer(
        "📅 Sana (01.01.2025 formatida) kiriting yoki <b>Bugun</b> tugmasini bosing:",
        reply_markup=get_date_select_inline_kb(),
        parse_mode="HTML"
    )


# ============================================================
# 4) SANA → AVTOMATIK RASM QABUL QILISH BOSHLANADI
# ============================================================

@router.callback_query(ActivityAddStates.DATE, F.data == "date_today")
async def add_date_inline(call: CallbackQuery, state: FSMContext):
    
    today_str = datetime.now().strftime("%d.%m.%Y")
    await state.update_data(date=today_str)
    
    await state.set_state(ActivityAddStates.PHOTOS)
    
    # Save/Cancel buttons
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="activity_save_final")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="activity_cancel")]
        ]
    )
    
    # Textda so'ralgandek, eski xabarni o'chirish yoki edit qilish mumkin.
    # Lekin "Bugun" bosilganda edit qilib qo'yish chiroyli:
    try:
        await call.message.edit_text(
            f"📅 Sana: <b>{today_str}</b>\n\n"
            f"🖼 Endi rasmlar yuborishingiz mumkin.\n"
            f"Maksimum <b>{MAX_IMAGES}</b> ta.\n\n"
            f"Agar rasm yubormasangiz → pastdagi <b>Saqlash</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=kb
        )
    except Exception:
        pass
        
    await call.answer()


@router.message(ActivityAddStates.DATE)
async def add_date(message: Message, state: FSMContext):

    text_val = message.text.strip()
    
    # 1) Check for "Bugun" (Today)
    if text_val == "📅 Bugun" or text_val.lower() == "bugun":
        date_str = datetime.now().strftime("%d.%m.%Y")
    else:
        date_str = text_val
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str):
            return await message.answer(
                "❌ Sana formati noto‘g‘ri!\nMasalan: 01.01.2025 yoki '📅 Bugun' tugmasini bosing.",
                reply_markup=get_date_select_inline_kb()
            )

    # Remove Reply Keyboard
    try:
         # Hack to remove reply keyboard without sending a separate message if possible, 
         # but we usually need to send a message. 
         # We are sending the next message anyway (Photos instruction), so we can attach ReplyKeyboardRemove there?
         # No, InlineKeyboard and ReplyKeyboard cannot be on same message.
         # So we send a "accepted" message or just delete the keyboard with a temp message.
         temp = await message.answer("...", reply_markup=ReplyKeyboardRemove())
         await temp.delete()
    except:
        pass
    
    # Also delete the user's "Bugun" message to keep it clean (optional but good)
    # try:
    #     await message.delete()
    # except:
    #     pass

    await state.update_data(date=date_str)
    await state.set_state(ActivityAddStates.PHOTOS)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="activity_save_final")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="activity_cancel")]
        ]
    )

    await message.answer(
        f"🖼 Endi rasmlar yuborishingiz mumkin.\n"
        f"Maksimum <b>{MAX_IMAGES}</b> ta.\n\n"
        f"Agar rasm yubormasangiz → pastdagi <b>Saqlash</b> tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=kb
    )


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

MAX_IMAGES = 5


# ============================================================
# 5) RASMLARNI QABUL QILISH (0–5)
# ============================================================
@router.message(ActivityAddStates.PHOTOS)
async def collect_photos(message: Message, state: FSMContext):

    data = await state.get_data()
    images = data.get("images", [])
    progress_msg_id = data.get("progress_msg_id")

    # ❗ LIMIT TEKSHIRISH
    if len(images) >= MAX_IMAGES:
        return await message.answer("❗️ 5 ta rasm limiti tugadi. 'Saqlash' tugmasini bosing.")

    # ❗ Faqat rasm qabul qilamiz
    if not message.photo:
        return await message.answer("❗️ Faqat rasm yuboring yoki 'Saqlash' tugmasini bosing.")

    # Rasmni saqlaymiz
    images.append(message.photo[-1].file_id)
    await state.update_data(images=images)

    # Tugmalar
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="activity_save_final")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="activity_cancel")]
        ]
    )

    progress_text = f"📸 Rasmlar qabul qilinyapti... ({len(images)}/{MAX_IMAGES})"

    # 📌 Birinchi rasm kelganida — XABAR YARATAMIZ
    if not progress_msg_id:
        sent_msg = await message.answer(progress_text, reply_markup=kb)
        await state.update_data(progress_msg_id=sent_msg.message_id)
    else:
        # 📌 Keyingi rasmlar kelganda — O‘SHA XABARNI TAHRIR QILAMIZ
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=progress_msg_id,
                text=progress_text,
                reply_markup=kb
            )
        except Exception:
            # Xatolik bo‘lsa ham jarayon davom etadi
            pass

    # ❗ Talaba yuborgan rasmlarning o‘zini o‘chirib tashlaymiz (chat toza bo‘lsin)
    try:
        await message.delete()
    except:
        pass



# ============================================================
# 6) SAQLASH
# ============================================================

@router.callback_query(F.data == "activity_save_final", ActivityAddStates.PHOTOS)
async def save_activity(call: CallbackQuery, state: FSMContext, session: AsyncSession):

    data = await state.get_data()
    images = data.get("images", [])

    tg_acc = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == call.from_user.id)
    )

    new_act = UserActivity(
        student_id=tg_acc.student_id,
        category=data["category"],
        name=data["name"],
        description=data["description"],
        date=data["date"],
        status="pending"
    )

    session.add(new_act)
    await session.flush()

    for img in images:
        session.add(UserActivityImage(
            activity_id=new_act.id,
            file_id=img,
            file_type="photo"
        ))

    await session.commit()
    await state.clear()

    from handlers.student.navigation import show_student_main_menu
    await show_student_main_menu(call, session, state, text="✅ Faollik muvaffaqiyatli qo‘shildi!")
    await call.answer()


# ============================================================
# 7) BEKOR QILISH
# ============================================================

@router.callback_query(F.data == "activity_cancel")
async def cancel_activity(call: CallbackQuery, state: FSMContext):

    await state.clear()
    from handlers.student.navigation import show_student_main_menu
    await show_student_main_menu(call, session, state, text="❌ Faollik qo‘shish bekor qilindi.")
    await call.answer()

# ============================================================
# 8) MOBILE APP UPLOAD HANDLER
# ============================================================
from models.states import ActivityUploadState
from database.models import PendingUpload

@router.message(ActivityUploadState.waiting_for_photo, F.photo)
async def on_mobile_upload_photo(message: Message, state: FSMContext, session: AsyncSession):
    allowed, _, _ = await check_premium_access(message.from_user.id, session)
    if not allowed:
        return await message.answer("Premium obuna talab etiladi.")

    student = await get_student_by_tg(message.from_user.id, session)
    if not student:
        return await message.answer("Siz talaba emassiz.")

    # Find active pending upload for this student
    # We find the latest one created within reasonable time (e.g., 24h)
    # The previous logic (file_id.is_(None)) is invalid now since we append.
    pending = await session.scalar(
        select(PendingUpload)
        .where(PendingUpload.student_id == student.id)
        .order_by(PendingUpload.created_at.desc())
        .limit(1)
    )

    if not pending:
        await state.clear()
        return await message.answer("Hozirda faol rasm yuklash so'rovi mavjud emas.")

    # Get current IDs
    current_ids = [fid for fid in pending.file_ids.split(",") if fid] if pending.file_ids else []
    
    if len(current_ids) >= 5:
        await state.clear()
        return await message.answer("✅ <b>Maksimal rasm soni (5) ga yetildi!</b>\n\nEndi ilovada davom etishingiz mumkin.")

    # Save File ID
    file_id = message.photo[-1].file_id
    current_ids.append(file_id)
    
    count = len(current_ids)
    
    if count == 5:
         await message.answer(f"✅ <b>Rasm qabul qilindi ({count}/5)</b>\n\nCheklovga yetildi. Ilovada davom eting.")
         await state.clear()
    else:
         await message.answer(f"✅ <b>Rasm qabul qilindi ({count}/5)</b>\n\nYana {5-count} ta rasm yuborishingiz mumkin.")

    # Update DB
    pending.file_ids = ",".join(current_ids)
    await session.commit()


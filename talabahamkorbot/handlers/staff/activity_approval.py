
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from keyboards.inline_kb import (
    get_activity_approve_kb, 
    get_activity_post_action_kb,
    get_rahbariyat_main_menu_kb,
    get_dekanat_main_menu_kb,
    get_tutor_main_menu_kb,
    get_start_role_inline_kb,
    get_staff_activity_history_kb,
    get_staff_activity_images_back_kb
)
from aiogram.types import InputMediaPhoto
from database.models import UserActivity, Student, Staff, StaffRole, TgAccount, UserActivityImage

router = Router()

# ===========================
#   HELPERS
# ===========================

async def get_staff_from_tg(user_id: int, session: AsyncSession) -> Staff | None:
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == user_id)
    )
    if not tg or not tg.staff_id:
        return None
    return await session.get(Staff, tg.staff_id)


async def send_activity_review(message: Message, activity: UserActivity, session: AsyncSession):
    student = await session.get(Student, activity.student_id)
    
    caption = (
        f"📌 <b>Faollik #{activity.id}</b>\n\n"
        f"👤 <b>{student.full_name}</b>\n"
        f"👥 Guruh: {student.group_number}\n"
        f"📂 Kategoriya: {activity.category}\n"
        f"📝 Nomi: {activity.name}\n"
        f"📅 Sana: {activity.date}\n"
        f"ℹ️ Tavsif: {activity.description or '—'}\n\n"
        f"Holat: {activity.status}"
    )
    
    kb = get_activity_approve_kb(activity.id)

    # Activity Image (agar bor bo'lsa)
    # Hozircha UserActivityImage alohida jadvalda.
    # Biz soddalik uchun birinchi rasmni olamiz agar bo'lsa.
    # UserActivity relationship: images
    
    # Relationshipni yuklash kerak edi.
    # send_activity_review chaqirilishidan oldin selectinload(UserActivity.images) qilish kerak.
    
    if activity.images:
        # Birinchi rasmni yuborish
        file_id = activity.images[0].file_id
        if activity.images[0].file_type == "photo":
            await message.answer_photo(file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
        else:
             await message.answer_document(file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=kb)


# ===========================
#   KOMANDALAR / HANDLERLAR
# ===========================

@router.callback_query(F.data.in_({"rahb_activity_approve_menu", "dek_activity_approve_menu", "tutor_activity_approve_menu"}))
async def start_activity_review(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    
    staff = await get_staff_from_tg(call.from_user.id, session)
    if not staff:
        await call.answer("Xodim topilmadi", show_alert=True)
        return

    # Filter logic
    stmt = select(UserActivity).options(selectinload(UserActivity.images)).where(UserActivity.status == "pending")

    if staff.role == StaffRole.RAHBARIYAT:
        # Rahbariyat hammasini ko'radi (User request confirmed)
        pass
    
    elif staff.role == StaffRole.DEKANAT:
        # Dekanat: UserActivity -> Student -> Faculty Check
        stmt = stmt.join(Student).where(Student.faculty_id == staff.faculty_id)
        
    elif staff.role == StaffRole.TYUTOR:
        # Tyutor: UserActivity -> Student -> Group Check
        # Tyutorning guruhlarini olishimiz kerak.
        # Staff modelida tutor_groups relationship bor.
        # Lekin biz Staff ni sessiondan olganimizda options bo'lmagani uchun lazy load xato berishi mumkin.
        # Qayta yuklaymiz
        staff_full = await session.get(Staff, staff.id, options=[selectinload(Staff.tutor_groups)])
        my_groups = [g.group_number for g in staff_full.tutor_groups]
        
        if not my_groups:
             await call.answer("Sizga guruhlar biriktirilmagan", show_alert=True)
             return
             
        stmt = stmt.join(Student).where(Student.group_number.in_(my_groups))
        
    else:
        await call.answer("Ruxsatsiz kirish", show_alert=True)
        return

    stmt = stmt.order_by(UserActivity.created_at)
    activities = (await session.scalars(stmt)).all()
    
    if not activities:
        # Bosh menyu tugmasi
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="activity_back")]
        ])
        await call.message.edit_text("📭 Tasdiqlash uchun yangi faolliklar yo'q.", reply_markup=kb)
        await call.answer()
        return

    # Start Review Loop
    await state.set_state(StaffActivityApproveStates.reviewing)
    await state.update_data(act_ids=[a.id for a in activities], index=0)

    # Birinchisini yuborish
    # Eski menyuni o'chirish yoki edit qilish. Rasm bilan bo'lsa yangi xabar afzal.
    await call.message.delete()
    await send_activity_review(call.message, activities[0], session)
    await call.answer()


@router.callback_query(F.data.startswith("staff_review_activities:"))
async def start_student_activity_review(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    student_id = int(call.data.split(":")[1])
    
    # Check if student exists & get details
    student = await session.get(Student, student_id)
    if not student:
        await call.answer("Talaba topilmadi", show_alert=True)
        return

    # Count stats
    stmt = select(UserActivity.status, func.count(UserActivity.id))\
        .where(UserActivity.student_id == student_id)\
        .group_by(UserActivity.status)
    
    stats_res = await session.execute(stmt)
    stats = dict(stats_res.all())
    
    pending_count = stats.get("pending", 0)
    confirmed_count = stats.get("confirmed", 0)
    rejected_count = stats.get("rejected", 0)
    
    msg_text = (
        f"📂 <b>Faolliklar holati:</b>\n\n"
        f"✅ Tasdiqlangan: <b>{confirmed_count}</b>\n"
        f"❌ Rad etilgan: <b>{rejected_count}</b>\n"
        f"⏳ Kutilmoqda: <b>{pending_count}</b>\n\n"
        "Quyidagi tugmalar orqali batafsil ko'rishingiz mumkin:"
    )

    # Build Keyboard
    kb_buttons = []
    
    # "Review Pending" button logic
    if pending_count > 0:
        kb_buttons.append([
            InlineKeyboardButton(
                text=f"📝 Tasdiqlash ({pending_count})", 
                callback_data=f"staff_review_pending_start:{student_id}"
            )
        ])
    
    # "History" button - Now Enabled
    kb_buttons.append([InlineKeyboardButton(text="📜 Tarixni ko'rish", callback_data=f"staff_activity_history:{student_id}")])

    # Back to Profile
    kb_buttons.append([
        InlineKeyboardButton(text="⬅️ Ortga (Profil)", callback_data=f"staff_back_to_profile:{student_id}")
    ])
    
    await call.message.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("staff_review_pending_start:"))
async def start_student_pending_review(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    student_id = int(call.data.split(":")[1])
    
    stmt = select(UserActivity).options(selectinload(UserActivity.images)).where(
        UserActivity.student_id == student_id,
        UserActivity.status == "pending"
    ).order_by(UserActivity.created_at)
    
    activities = (await session.scalars(stmt)).all()
    
    if not activities:
         await call.answer("⚠️ Tasdiqlash uchun faolliklar qolmadi.", show_alert=True)
         # Refresh summary
         await start_student_activity_review(call, session, state)
         return

    # Start Review Loop
    await state.set_state(StaffActivityApproveStates.reviewing)
    await state.update_data(act_ids=[a.id for a in activities], index=0)
    
    await call.message.delete()
    await send_activity_review(call.message, activities[0], session)
    await call.answer()


# Refactoring approve/reject signatures to include state
import html
import logging

# ... imports ...

@router.callback_query(F.data.startswith("activity_yes:"))
async def approve_activity_wrapper(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    logging.info(f"Approve clicked: {call.data}")
    act_id = int(call.data.split(":")[1])
    updated = await _update_status(session, act_id, "confirmed")
    
    if updated:
        # 1. Loadingni to'xtatish (Eng muhimi!)
        await call.answer("✅ Tasdiqlandi")
        
        # 2. Yangi xabar yuborish
        await call.message.answer(
            text="✅ <b>USHBU FAOLLIK TASDIQLANDI (YANGI)</b>",
            parse_mode="HTML",
            reply_markup=get_activity_post_action_kb()
        )
        
        # 3. Eski xabarni tozalash (Ixtiyoriy, keyin bo'lsa ham mayli)
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.warning(f"Could not remove markup: {e}")
            
    else:
        await call.answer("Xatolik: Baza yangilanmadi", show_alert=True)


@router.callback_query(F.data.startswith("activity_no:"))
async def reject_activity_wrapper(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    logging.info(f"Reject clicked: {call.data}")
    act_id = int(call.data.split(":")[1])
    updated = await _update_status(session, act_id, "rejected")
    
    if updated:
        await call.answer("❌ Rad etildi")

        await call.message.answer(
            text="❌ <b>USHBU FAOLLIK RAD ETILDI (YANGI)</b>",
            parse_mode="HTML",
            reply_markup=get_activity_post_action_kb()
        )
        
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.warning(f"Could not remove markup: {e}")
            
    else:
        await call.answer("Xatolik: Baza yangilanmadi", show_alert=True)

@router.callback_query(F.data == "activity_next")
async def next_activity_btn(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    # Eski xabarni o'chirish (agar kerak bo'lsa, clean UI uchun)
    try:
        await call.message.delete()
    except:
        pass
    await _show_next(call, session, state)

@router.callback_query(F.data == "activity_back")
async def back_to_menu(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    await call.message.delete()
    
    # Rolni aniqlash va menyu yuborish
    staff = await get_staff_from_tg(call.from_user.id, session)
    if not staff:
        await call.message.answer("Bosh sahifa", reply_markup=get_start_role_inline_kb())
        return

    if staff.role == StaffRole.RAHBARIYAT:
        await call.message.answer("🏛 Rahbariyat menyusi", reply_markup=get_rahbariyat_main_menu_kb())
    elif staff.role == StaffRole.DEKANAT:
        await call.message.answer("🏫 Dekanat menyusi", reply_markup=get_dekanat_main_menu_kb())
    elif staff.role == StaffRole.TYUTOR:
        await call.message.answer("🧑‍🏫 Tyutor menyusi", reply_markup=get_tutor_main_menu_kb())
    else:
        await call.message.answer("Menyu", reply_markup=get_start_role_inline_kb())


# Internal Helpers
async def _update_status(session, act_id, status):
    activity = await session.get(UserActivity, act_id)
    if activity:
        activity.status = status
        await session.commit()
        return True
    return False

async def _show_next(call, session, state):
    data = await state.get_data()
    act_ids = data.get("act_ids", [])
    index = data.get("index", 0)
    
    # Current index was just processed, so move to next
    new_index = index + 1
    
    if new_index >= len(act_ids):
        # Bosh menyu tugmasi
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="activity_back")]
        ])
        await call.message.answer("✅ Barcha faolliklar ko'rib chiqildi!", reply_markup=kb)
        await state.clear()
        return
        
    await state.update_data(index=new_index)
    
    # Fetch next
    activity = await session.get(UserActivity, act_ids[new_index])
    # Rasmlarni yuklash
    # Session get lazy load qiladi, activity.images da error berishi mumkin agar session yopilsa, lekin bu yerda ochiq.
    # selectinload ishlatish xavfsizroq.
    activity = await session.execute(select(UserActivity).options(selectinload(UserActivity.images)).where(UserActivity.id == act_ids[new_index]))
    activity = activity.scalar_one_or_none()
    
    if activity:
        # Message object kerak send_activity_review uchun. Call.message bor.
        await send_activity_review(call.message, activity, session)
    else:
        # Agar activity topilmasa (o'chirilgan bo'lsa), keyingisiga o'tish
        await _show_next(call, session, state)


# ===========================
#   XODIM UCHUN SCOL HISTORY
# ===========================

@router.callback_query(F.data.startswith("staff_activity_history:"))
async def staff_view_history_start(call: CallbackQuery, session: AsyncSession):
    student_id = int(call.data.split(":")[1])
    
    student = await session.get(Student, student_id)
    if not student:
        await call.answer("Talaba topilmadi", show_alert=True)
        return

    # Fetch all activities
    acts = await session.scalars(
        select(UserActivity)
        .where(UserActivity.student_id == student_id)
        .order_by(UserActivity.id.desc())
    )
    acts = acts.all()

    if not acts:
        await call.answer("Faolliklar mavjud emas!", show_alert=True)
        return

    text = f"📋 <b>{student.full_name} faolliklari ({len(acts)} ta):</b>\n"

    for i, a in enumerate(acts, start=1):
        status_emoji = "⏳" if a.status == "pending" else ("✅" if a.status == "confirmed" else "❌")
        
        text += (
            f"\n<b>{i}) {a.category.capitalize()} (#{a.id})</b>\n"
            f"🏷 Nomi: <b>{a.name}</b>\n"
            f"📝 Tavsif: {a.description}\n"
            f"📅 Sana: <code>{a.date}</code>\n"
            f"📌 Status: {status_emoji} <b>{a.status}</b>\n"
        )
        
    # Telegram limit checks (basic)
    if len(text) > 4000:
        text = text[:4000] + "\n...(davomi kesildi)"

    await call.message.edit_text(
        text,
        reply_markup=get_staff_activity_history_kb(student_id),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("staff_activity_images:"))
async def staff_view_history_images(call: CallbackQuery, session: AsyncSession):
    student_id = int(call.data.split(":")[1])
    
    # Fetch all activities
    acts = await session.scalars(
        select(UserActivity)
        .where(UserActivity.student_id == student_id)
        .order_by(UserActivity.id)
    )
    acts = acts.all()

    if not acts:
        await call.answer("Faolliklar yo'q", show_alert=True)
        return

    await call.answer()
    
    # Iterate and show images
    has_images = False
    for act in acts:
        imgs = await session.scalars(
            select(UserActivityImage)
            .where(UserActivityImage.activity_id == act.id)
        )
        imgs = imgs.all()

        if not imgs:
            continue
            
        has_images = True

        caption = (
            f"<b>{act.category.capitalize()} (#{act.id})</b>\n"
            f"Nomi: <b>{act.name}</b>\n"
            f"Status: <b>{act.status}</b>"
        )

        if len(imgs) == 1:
            await call.message.answer_photo(
                imgs[0].file_id,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            media = []
            for i, img in enumerate(imgs):
                if i == 0:
                    media.append(InputMediaPhoto(media=img.file_id, caption=caption, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=img.file_id))
            await call.message.answer_media_group(media)

    if not has_images:
        await call.message.answer("🖼 Ushbu talabada rasmli faolliklar yo'q.")

    # Back button message
    await call.message.answer(
        "⬅️ Ortga qaytish",
        reply_markup=get_staff_activity_images_back_kb(student_id)
    )

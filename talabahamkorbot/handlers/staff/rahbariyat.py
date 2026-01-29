from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.states import RahbAppealStates
from database.models import UserAppeal
from keyboards.inline_kb import get_rh_feedback_kb

from models.states import RahbBroadcastStates
from database.models import Staff, TgAccount, Student, TutorGroup, StaffRole

from keyboards.inline_kb import (
    get_rahbariyat_main_menu_kb,
    get_rahb_activity_menu_kb,
    get_student_lookup_back_kb,
    get_rahb_broadcast_confirm_kb,
    get_rahb_broadcast_back_kb,
    get_rahb_appeal_actions_kb,
    get_rahb_assign_choice_kb,
    get_rahb_post_reply_kb,
    get_rahb_post_reply_kb,
    get_student_feedback_reply_kb,
)
from utils.feedback_utils import get_feedback_thread_text

router = Router()

# ============================================================
# 1) RAHBARIYAT ASOSIY MENYUSI
# ============================================================
@router.callback_query(F.data == "rahb_menu")
async def rahbariyat_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "🏛 <b>Rahbariyat bo‘limi</b>\nQuyidagi bo‘limlardan birini tanlang:",
        reply_markup=get_rahbariyat_main_menu_kb(),
        parse_mode="HTML",
    )
    await call.answer()


# ============================================================
# 2) UNIVERSITET BO‘YICHA E’LON — BOSHLASH
# ============================================================
@router.callback_query(F.data == "rahb_broadcast")
async def rahb_broadcast_start(call: CallbackQuery, state: FSMContext):
    print(f"DEBUG: rahb_broadcast_start called by {call.from_user.id}")
    await state.clear()
    await state.set_state(RahbBroadcastStates.WAITING_CONTENT)

    await call.message.edit_text(
        "📣 <b>Universitet bo‘yicha e’lon yuborish</b>\n\n"
        "Siz bu yerda <b>butun universitetga</b> xabar yuborishingiz mumkin.\n\n"
        "✍️ Matn, rasm, video, voice yoki fayl yuboring.",
        parse_mode="HTML",
        reply_markup=get_rahb_broadcast_back_kb(),
    )
    await call.answer()


# ============================================================
# 3) E’LON MAZMUNI QABUL QILISH
# ============================================================
@router.message(RahbBroadcastStates.WAITING_CONTENT)
async def rahb_broadcast_receive(message: Message, state: FSMContext):
    data = {
        "text": message.caption or message.text,
        "file_id": None,
        "file_type": None,
    }

    if message.photo:
        data["file_id"] = message.photo[-1].file_id
        data["file_type"] = "photo"
    elif message.video:
        data["file_id"] = message.video.file_id
        data["file_type"] = "video"
    elif message.voice:
        data["file_id"] = message.voice.file_id
        data["file_type"] = "voice"
    elif message.document:
        data["file_id"] = message.document.file_id
        data["file_type"] = "document"

    await state.update_data(**data)
    await state.set_state(RahbBroadcastStates.CONFIRM)

    await message.answer(
        "📨 <b>Xabar tayyor.</b>\n\n"
        "Yuborishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=get_rahb_broadcast_confirm_kb(),
    )


# ============================================================
# 4) E’LONNI TASDIQLASH VA YUBORISH
# ============================================================
@router.callback_query(
    RahbBroadcastStates.CONFIRM,
    F.data == "rahb_broadcast_confirm",
)
async def rahb_broadcast_confirm(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    data = await state.get_data()

    staff = await session.scalar(
        select(Staff)
        .join(TgAccount)
        .where(TgAccount.telegram_id == call.from_user.id)
    )

    if not staff:
        await call.answer("❌ Xodim aniqlanmadi", show_alert=True)
        return

    students = await session.scalars(
        select(TgAccount.telegram_id)
        .join(Student)
        .where(Student.university_id == staff.university_id)
    )

    bot = call.bot
    sent = 0

    for tg_id in students.all():
        try:
            if data["file_id"]:
                if data["file_type"] == "photo":
                    await bot.send_photo(tg_id, data["file_id"], caption=data["text"])
                elif data["file_type"] == "video":
                    await bot.send_video(tg_id, data["file_id"], caption=data["text"])
                elif data["file_type"] == "voice":
                    await bot.send_voice(tg_id, data["file_id"])
                elif data["file_type"] == "document":
                    await bot.send_document(tg_id, data["file_id"], caption=data["text"])
            else:
                await bot.send_message(tg_id, data["text"])
            sent += 1
        except Exception:
            continue

    await state.clear()

    await call.message.edit_text(
        f"✅ <b>E’lon yuborildi</b>\n\n"
        f"👥 Yetib borganlar soni: <b>{sent}</b>",
        parse_mode="HTML",
        reply_markup=get_rahbariyat_main_menu_kb(),
    )
    await call.answer()


# ============================================================
# 5) BEKOR QILISH → YANA XABAR KIRITISH
# ============================================================
@router.callback_query(
    RahbBroadcastStates.CONFIRM,
    F.data == "rahb_broadcast_cancel",
)
async def rahb_broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.set_state(RahbBroadcastStates.WAITING_CONTENT)

    await call.message.edit_text(
        "❌ Xabar bekor qilindi.\n\n"
        "✍️ Yangi xabar yuboring:",
        reply_markup=get_rahb_broadcast_back_kb(),
    )
    await call.answer()

# ============================================================
# 6) Talaba murojaatlari
# ============================================================

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import (
    Student,
    StudentFeedback,
    Staff,
    TgAccount,
    TutorGroup,
    StaffRole,
    FeedbackReply
)

from models.states import RahbAppealStates
from keyboards.inline_kb import get_rahb_appeal_actions_kb

async def get_staff_from_tg(tg_id: int, session: AsyncSession) -> Staff | None:
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == tg_id)
    )
    if not tg or not tg.staff_id:
        return None
    return await session.get(Staff, tg.staff_id)

@router.callback_query(F.data == "rh_feedback")
async def rahb_view_appeals(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    staff = await get_staff_from_tg(call.from_user.id, session)
    if not staff:
        await call.answer("❌ Xodim aniqlanmadi", show_alert=True)
        return

    appeals = await session.scalars(
        select(StudentFeedback)
        .join(Student)
        .where(
            Student.university_id == staff.university_id,
            StudentFeedback.status == "pending"
        )
        .order_by(StudentFeedback.created_at.asc())
    )

    appeals = appeals.all()

    if not appeals:
        await call.message.edit_text("📭 Yangi murojaatlar yo‘q.")
        await call.answer()
        return

    await state.set_state(RahbAppealStates.viewing)
    await state.update_data(
        appeal_ids=[a.id for a in appeals],
        index=0
    )

    await send_appeal(call, appeals[0], session)
    await call.answer()

async def send_appeal(call: CallbackQuery, appeal: StudentFeedback, session: AsyncSession):
    # Studentni fakultet bilan birga yuklaymiz
    student = await session.scalar(
        select(Student)
        .options(selectinload(Student.faculty))
        .where(Student.id == appeal.student_id)
    )

    faculty_name = student.faculty.name if student.faculty else "Noma'lum"

    from config import OWNER_TELEGRAM_ID
    is_owner = (call.from_user.id == OWNER_TELEGRAM_ID)

    # Anonimlikni tekshirish
    if appeal.is_anonymous and not is_owner:
        display_name = "🕵️‍♂️ Anonim"
        display_faculty = "---"
        display_group = "---"
        display_hemis = "---"
    else:
        # Agar owner bo'lsa va anonim bo'lsa, bildirishnoma qo'shamiz
        owner_note = " (👁 OWNER)" if (appeal.is_anonymous and is_owner) else ""
        
        display_name = f"<b>{student.full_name}</b>{owner_note}"
        display_faculty = f"<b>{faculty_name}</b>"
        display_group = f"<b>{student.group_number or 'Kiritilmagan'}</b>"
        display_hemis = f"<code>{student.hemis_login}</code>"

    text = (
        "📨 <b>Talaba murojaati</b>\n\n"
        f"👤 Talaba: {display_name}\n"
        f"🎓 Fakultet: {display_faculty}\n"
        f"👥 Guruh: {display_group}\n"
        f"🆔 HEMIS: {display_hemis}\n\n"
        f"{appeal.text or ''}"
    )

    kb = get_rahb_appeal_actions_kb(appeal.id)

    if appeal.file_id:
        if appeal.file_type == "photo":
            await call.message.answer_photo(
                appeal.file_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        elif appeal.file_type == "document":
            await call.message.answer_document(
                appeal.file_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)



@router.callback_query(F.data.startswith("rahb_reply:"), RahbAppealStates.viewing)
async def rahb_reply_start(call: CallbackQuery, state: FSMContext):
    appeal_id = int(call.data.split(":")[1])
    await state.update_data(reply_appeal_id=appeal_id)
    await state.set_state(RahbAppealStates.replying)
    await call.message.answer("📝 <b>Javob matnini kiriting:</b>", parse_mode="HTML")
    await call.answer()

@router.message(RahbAppealStates.replying)
async def rahb_reply_send(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    appeal_id = data.get("reply_appeal_id")
    appeal = await session.get(StudentFeedback, appeal_id)
    
    if not appeal:
        await message.answer("❌ Murojaat topilmadi.")
        await state.clear()
        return

    # Xodim ma'lumotlarini olish
    staff = await session.scalar(
        select(Staff)
        .join(TgAccount)
        .where(TgAccount.telegram_id == message.from_user.id)
    )

    if not staff:
        await message.answer("❌ Xodim aniqlanmadi (Bazadan).")
        return

    # Talabaga yuborish
    student = await session.get(Student, appeal.student_id)
    tg_account = await session.scalar(select(TgAccount).where(TgAccount.student_id == student.id))

    if tg_account:
        try:
            # Javobni saqlash (Avval saqlaymiz, keyin history generatsiya qilamiz)
            reply_entry = FeedbackReply(
                feedback_id=appeal.id,
                staff_id=staff.id,
                text=message.text
            )
            session.add(reply_entry)
            await session.commit() # ID olish va vaqt tushishi uchun
            
            # DB update (Status)
            appeal.status = "answered"
            appeal.assigned_staff_id = staff.id
            appeal.assigned_role = staff.role
            await session.commit()

            # To'liq tarixni shakllantirish
            history_text = await get_feedback_thread_text(appeal.id, session)

            await message.bot.send_message(
                tg_account.telegram_id,
                history_text,
                parse_mode="HTML",
                reply_markup=get_student_feedback_reply_kb(appeal.id)
            )
            
            await message.answer(
                "✅ Javob yuborildi!",
                reply_markup=get_rahb_post_reply_kb(appeal_id)
            )
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")
    else:
        await message.answer("❌ Talabaning Telegrami topilmadi.")

    # Ortga qaytish
    await state.set_state(RahbAppealStates.viewing)


@router.callback_query(F.data.startswith("rahb_assign:"))
async def rahb_assign_choice(call: CallbackQuery):
    appeal_id = int(call.data.split(":")[1])
    await call.message.edit_reply_markup(reply_markup=get_rahb_assign_choice_kb(appeal_id))
    await call.answer()

@router.callback_query(F.data.startswith("rahb_assign_dekanat:"))
async def rahb_assign_dekanat(call: CallbackQuery, session: AsyncSession):
    appeal_id = int(call.data.split(":")[1])
    appeal = await session.get(StudentFeedback, appeal_id)
    student = await session.get(Student, appeal.student_id)

    # Fakultet dekanat xodimlarini topish
    staffs = await session.scalars(
        select(Staff)
        .where(
            Staff.role == StaffRole.DEKANAT,
            Staff.faculty_id == student.faculty_id,
            Staff.is_active == True
        )
    )
    staffs = staffs.all()

    if not staffs:
        await call.answer("❌ Bu fakultetda dekanat xodimlari topilmadi", show_alert=True)
        return

    count = 0
    for staff in staffs:
        tg = await session.scalar(select(TgAccount).where(TgAccount.staff_id == staff.id))
        if tg:
            try:
                await call.bot.send_message(
                    tg.telegram_id,
                    "📨 <b>Yangi murojaat biriktirildi!</b>\nIltimos, botga kirib tekshiring."
                )
                count += 1
            except:
                pass
    
    appeal.assigned_role = StaffRole.DEKANAT
    appeal.status = "assigned_dekanat"
    await session.commit()

    await call.answer(f"✅ {count} ta dekanat xodimiga yuborildi", show_alert=True)
    await call.message.delete()


@router.callback_query(F.data.startswith("rahb_assign_tyutor:"))
async def rahb_assign_tutor(call: CallbackQuery, session: AsyncSession):
    appeal_id = int(call.data.split(":")[1])
    appeal = await session.get(StudentFeedback, appeal_id)
    student = await session.get(Student, appeal.student_id)

    # Guruh tyutorini topish
    tutor_group = await session.scalar(
        select(TutorGroup).where(TutorGroup.name == student.group_number)
    )
    
    if not tutor_group or not tutor_group.tutor_id:
        await call.answer("❌ Bu guruhga tyutor biriktirilmagan", show_alert=True)
        return

    tutor = await session.get(Staff, tutor_group.tutor_id)
    tg = await session.scalar(select(TgAccount).where(TgAccount.staff_id == tutor.id))

    if tg:
        try:
            await call.bot.send_message(
                tg.telegram_id,
                "📨 <b>Sizga yangi murojaat biriktirildi!</b>\nIltimos, botga kirib tekshiring."
            )
        except:
            pass

    appeal.assigned_role = StaffRole.TYUTOR
    appeal.assigned_staff_id = tutor.id
    appeal.status = "assigned_tyutor"
    await session.commit()

    await call.answer(f"✅ Tyutor {tutor.full_name} ga biriktirildi", show_alert=True)
    await call.message.delete()

@router.callback_query(F.data.startswith("rahb_appeal_next:"), RahbAppealStates.viewing)
async def rahb_appeal_next(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    appeal_ids = data["appeal_ids"]
    index = data["index"] + 1

    if index >= len(appeal_ids):
        await call.answer("📭 Boshqa murojaat yo‘q", show_alert=True)
        return

    await state.update_data(index=index)

    appeal = await session.get(StudentFeedback, appeal_ids[index])
    await send_appeal(call, appeal, session)
    await call.answer()

async def assign_to_staff(call: CallbackQuery, state: FSMContext, role: str, identifier: str, session: AsyncSession):
    appeal_id = int(call.data.split(":")[1])

    appeal = await session.get(UserAppeal, appeal_id)
    student = await session.get(Student, appeal.student_id)

    # Belirli ro'lga qarab xodimni tanlash
    staff = await session.scalar(
        select(Staff).where(
            Staff.role == role,
            Staff.university_id == student.university_id,
            getattr(Staff, identifier) == getattr(student, identifier)
        )
    )

    if not staff:
        await call.answer(f"❌ Mos {role} topilmadi", show_alert=True)
        return

    appeal.assigned_role = role
    appeal.assigned_staff_id = staff.id
    appeal.status = f"assigned_{role}"

    await session.commit()

    # 🔔 Notification
    await call.bot.send_message(
        (await session.scalar(
            select(TgAccount.telegram_id)
            .where(TgAccount.staff_id == staff.id)
        )),
        f"📨 Sizga yangi murojaat biriktirildi ({role.capitalize()})."
    )

    await call.message.edit_text(f"✅ Murojaat {role}ga biriktirildi.")
    await state.clear()
    await call.answer()




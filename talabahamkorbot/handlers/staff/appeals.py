# handlers/staff/appeals.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from database.models import TgAccount, Staff, Student, StudentFeedback, FeedbackReply, StaffRole
from models.states import StaffAppealStates
from keyboards.inline_kb import get_staff_appeal_actions_kb, get_student_feedback_reply_kb
from utils.feedback_utils import get_feedback_thread_text
from services.ai_service import generate_reply_suggestion # AI Import

router = Router()


# ============================ Helper — Xodimni aniqlash ============================

async def get_staff_from_tg(user_id: int, session: AsyncSession) -> Staff | None:
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == user_id)
    )
    if not tg or not tg.staff_id:
        return None
    return await session.get(Staff, tg.staff_id)


# ======================= 1) Murojaatlar menyusiga kirish =======================

# Barcha rollar uchun umumiy kirish nuqtasi
# rh_feedback -> Rahbariyat
# dk_feedback -> Dekanat
# tt_feedback -> Tyutor
@router.callback_query(F.data.in_({"staff_view_appeals", "rh_feedback", "dk_feedback", "tt_feedback"}))
async def start_view_appeals(call: CallbackQuery, session: AsyncSession, state: FSMContext):

    staff = await get_staff_from_tg(call.from_user.id, session)
    if not staff:
        await call.answer("❌ Xodim sifatida ro‘yxatdan o‘tmagansiz.", show_alert=True)
        return

    # Filter Logic
    # 1. Yopilgan (closed) murojaatlar default holatda ko'rinmaydi
    stmt = select(StudentFeedback).where(StudentFeedback.status != "closed")

    if staff.role == StaffRole.RAHBARIYAT:
        # Rahbariyat: 'rahbariyat'ga biriktirilgan yoki 'pending' (yangi, hali hech kim olmagan)
        stmt = stmt.where(
            or_(
                StudentFeedback.assigned_role == StaffRole.RAHBARIYAT.value,
                StudentFeedback.status == "pending"
            )
        )
    elif staff.role == StaffRole.DEKANAT:
        # Dekanat: O'z fakultetidagi barcha (yopilmagan) murojaatlarni ko'rishi kerak
        stmt = stmt.join(Student).where(
            Student.faculty_id == staff.faculty_id
        )
    elif staff.role == StaffRole.TYUTOR:
        # Tyutor: Assigned role 'tyutor' VA (staff.id ga biriktirilgan murojaat)
        # Assign paytida assigned_staff_id aniq kiritilgan edi.
        stmt = stmt.where(
            StudentFeedback.assigned_role == StaffRole.TYUTOR.value,
            StudentFeedback.assigned_staff_id == staff.id
        )
    elif staff.role == StaffRole.TEACHER:
        # Teacher: Direct assign OR target_hemis_id match
        conds = [StudentFeedback.assigned_staff_id == staff.id]
        if staff.hemis_id:
            conds.append(StudentFeedback.target_hemis_id == staff.hemis_id)
            
        stmt = stmt.where(or_(*conds))
    else:
        # Default Logic: Check ownership by ID or legacy Role
        # If hemis_id exists, check loose coupling too
        conds = [StudentFeedback.assigned_staff_id == staff.id]
        if staff.hemis_id:
             conds.append(StudentFeedback.target_hemis_id == staff.hemis_id)
        
        # If role is generic
        if staff.role not in [StaffRole.TEACHER, StaffRole.TYUTOR]:
             # e.g. Buxgalter -> role assign check can be added if needed
             pass

        stmt = stmt.where(or_(*conds))

    # Tartib: Eng eskisi oldin (FIFO) queue prinsipi
    stmt = stmt.order_by(StudentFeedback.created_at)

    appeals = (await session.scalars(stmt)).all()
    
    if not appeals:
        await call.message.edit_text("📭 Hozircha yangi murojaatlar yo‘q.")
        await call.answer()
        return

    # 1-murojaatdan boshlaymiz
    await state.set_state(StaffAppealStates.viewing)
    
    # Safe Role Conversion
    role_str = staff.role.value if hasattr(staff.role, "value") else str(staff.role)

    # ID larni saqlab olamiz, keyingisiga o'tish oson bo'lishi uchun
    await state.update_data(appeal_ids=[a.id for a in appeals], index=0, role=role_str)

    await send_appeal(call.message, appeals[0], session, role_str)
    await call.answer()


@router.callback_query(F.data.startswith("staff_view_appeals:"))
async def start_student_appeals_review(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    student_id = int(call.data.split(":")[1])
    
    # Xodimni aniqlash
    staff = await get_staff_from_tg(call.from_user.id, session)
    if not staff:
        await call.answer("❌ Xodim aniqlanmadi.", show_alert=True)
        return

    # Talabaning barcha murojaatlarini yuklash
    stmt = select(StudentFeedback).where(StudentFeedback.student_id == student_id).order_by(StudentFeedback.created_at.desc())
    
    appeals = (await session.scalars(stmt)).all()
    
    if not appeals:
        await call.answer("📭 Bu talaba hali murojaat yubormagan.", show_alert=True)
        return

    # Review jarayonini boshlash
    role_str = staff.role.value if hasattr(staff.role, "value") else staff.role

    await state.set_state(StaffAppealStates.viewing)
    await state.update_data(appeal_ids=[a.id for a in appeals], index=0, role=role_str)

    # Birinchisini ko'rsatish
    await call.message.delete()
    await send_appeal(call.message, appeals[0], session, role_str)
    await call.answer()


# ================== 2) Murojaatni xodimga yuborish (universal) ==================

async def send_appeal(msg_or_call, appeal: StudentFeedback, session: AsyncSession, role: str = None):
    if hasattr(msg_or_call, "message"):
        msg = msg_or_call.message
    else:
        msg = msg_or_call

    student = await session.get(Student, appeal.student_id)
    history_text = await get_feedback_thread_text(appeal.id, session)

    # Talaba haqida qisqacha info + thread
    caption = (
        f"📨 <b>Murojaat #{appeal.id}</b>\n\n"
        f"👤 <b>{student.full_name}</b>\n"
        f"🆔 HEMIS: <code>{student.hemis_login}</code>\n"
        f"👥 Guruh: {student.group_number}\n\n"
        f"{history_text}"
    )
    
    # Telegram limiti 4096 (caption uchun 1024), ehtiyot bo'lish kerak.
    # Agar juda uzun bo'lsa, qisqartirish.
    if len(caption) > 1000:
        caption = caption[:1000] + "\n...(to'liq matn sig'madi)"

    kb = get_staff_appeal_actions_kb(appeal.id, role, student_id=appeal.student_id)

    # Agar oxirgi murojaatda file bo'lsa
    if appeal.file_id:
        try:
            if appeal.file_type == "photo":
                await msg.answer_photo(appeal.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
            elif appeal.file_type == "video":
                await msg.answer_video(appeal.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
            elif appeal.file_type == "document":
                await msg.answer_document(appeal.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
            else:
                 await msg.answer(caption, parse_mode="HTML", reply_markup=kb)
        except Exception:
            # Fayl eskirgan yoki xato bo'lsa, matn qilib yuboramiz
            await msg.answer(caption + "\n\n⚠️ Media faylni yuklab bo‘lmadi.", parse_mode="HTML", reply_markup=kb)
    else:
        await msg.answer(caption, parse_mode="HTML", reply_markup=kb)


# ============================ 3) "Keyingisi" tugmasi ============================

@router.callback_query(F.data == "appeal_next")
async def next_appeal(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    appeal_ids: list[int] = data.get("appeal_ids", [])
    index: int = data.get("index", 0)
    role: str = data.get("role", None)

    if not appeal_ids or index + 1 >= len(appeal_ids):
        await call.answer("📭 Boshqa murojaat qolmadi.", show_alert=True)
        return

    new_index = index + 1
    await state.update_data(index=new_index)

    appeal = await session.get(StudentFeedback, appeal_ids[new_index])
    if appeal:
        # Eski xabarni o'chirish (tozalik uchun)
        try:
            await call.message.delete()
        except:
            pass
        await send_appeal(call, appeal, session, role)
    else:
        await call.answer("⚠️ Murojaat topilmadi, keyingisiga o'tilmoqda.")
        # Murojaat o'chib ketgan bo'lsa, yana keyingisiga o'tamiz
        await next_appeal(call, session, state)

    await call.answer()


# ======================= 4) "Javob berish" tugmasi =======================

@router.callback_query(F.data.startswith("appeal_reply:"))
async def reply_to_appeal_start(call: CallbackQuery, state: FSMContext):
    _, raw_id = call.data.split(":")
    appeal_id = int(raw_id)

    await state.set_state(StaffAppealStates.replying)
    await state.update_data(current_appeal_id=appeal_id)

    await call.message.answer(
        "✍️ <b>Javob matnini yozing yoki fayl (rasm/video/hujjat) yuboring:</b>\n"
        "Sizning javobingiz to'g'ridan-to'g'ri talabaga yuboriladi.",
        parse_mode="HTML"
    )
    await call.answer()


@router.message(StaffAppealStates.replying)
async def save_reply(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    appeal_id = data.get("current_appeal_id")
    
    if not appeal_id:
        await message.answer("❌ Xatolik: Murojaat aniqlanmadi.")
        await state.clear()
        return

    appeal = await session.get(StudentFeedback, appeal_id)
    if not appeal:
        await message.answer("❌ Murojaat topilmadi.")
        await state.clear()
        return
        
    staff = await get_staff_from_tg(message.from_user.id, session)
    if not staff:
        await message.answer("❌ Xodim aniqlanmadi.")
        return

    # 1.1 Media faylni aniqlash
    file_id = None
    file_type = None
    input_text = message.text or message.caption

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    
    # Text ham, fayl ham yo'q bo'lsa
    if not input_text and not file_id:
        await message.answer("⚠️ Iltimos, matn yoki fayl yuboring.")
        return

    # 1. Javobni bazaga yozish
    reply = FeedbackReply(
        feedback_id=appeal.id,
        staff_id=staff.id,
        text=input_text,
        file_id=file_id,
        file_type=file_type
    )
    session.add(reply)
    
    # 2. Statusni yangilash
    appeal.status = "answered"
    # Agar Rahbariyat javob bersa, assign qilinmagan bo'lsa ham unga o'tadi
    if not appeal.assigned_staff_id:
         appeal.assigned_staff_id = staff.id
         
    await session.commit()
    
    # 3. Talabaga xabar berish (Push)
    tg_acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == appeal.student_id))
    if tg_acc:
        try:
           # Talabani o'z menusiga qaytarish uchun kb:
           # Lekin student_main_menu import qilish circular dependency berishi mumkin.
           # Shunchaki text yuboramiz.
           staff_role_name = staff.role.value.capitalize() if hasattr(staff.role, "value") else str(staff.role).capitalize()
           
           # To'liq threadni olamiz
           full_history = await get_feedback_thread_text(appeal.id, session)
           
           msg_text = (
               f"🔔 <b>Murojaatingizga javob keldi!</b>\n\n"
               f"👨‍💼 <b>{staff.full_name} ({staff_role_name}):</b>\n" # Xodim nomi va roli
               f"{full_history}\n"
               f"👇 Quyidagi tugmalar orqali murojaatni yopishingiz yoki qayta yozishingiz mumkin."
           )

           # Telegram limiti
           if len(msg_text) > 4096: # Caption limiti 1024, text 4096
               msg_text = msg_text[:1000] + "\n...(davomi kesildi)"

           kb = get_student_feedback_reply_kb(appeal.id)

           # Fayl bo'lsa fayl bilan, bo'lmasa matn
           if file_id:
               if file_type == "photo":
                   await message.bot.send_photo(tg_acc.telegram_id, file_id, caption=msg_text[:1024], parse_mode="HTML", reply_markup=kb)
               elif file_type == "video":
                   await message.bot.send_video(tg_acc.telegram_id, file_id, caption=msg_text[:1024], parse_mode="HTML", reply_markup=kb)
               elif file_type == "document":
                   await message.bot.send_document(tg_acc.telegram_id, file_id, caption=msg_text[:1024], parse_mode="HTML", reply_markup=kb)
           else:
               await message.bot.send_message(
                   tg_acc.telegram_id,
                   msg_text,
                   parse_mode="HTML",
                   reply_markup=kb
               )
        except Exception:
            pass

    await message.answer("✅ Javob muvaffaqiyatli yuborildi.")
    
    # State-ni yana reviewingga qaytarib qo'yamiz, 
    # lekin user 'Keyingisi' tugmasini bosishi uchun eski xabarga qaytishi kerak.
    # Yoki shunchaki tugatadi.
    await state.clear() 
    # Tozalab qo'yamiz, chunki "Javob berildi" -> Jarayon tugadi ushbu murojaat uchun.
    # User yana "Murojaatlar" menyusiga kirib davom etishi mumkin.

# ============================================================
#                  AI JAVOB (Smart Reply)
# ============================================================
import logging
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("staff_ai_reply:"))
async def cb_staff_ai_reply(call: CallbackQuery, session: AsyncSession):
    logger.info(f"AI Reply button clicked by user {call.from_user.id}")
    try:
        _, appeal_id_str = call.data.split(":", 1)
        appeal_id = int(appeal_id_str)
        logger.info(f"Processing AI reply for appeal {appeal_id}")
    except ValueError:
        logger.error("Failed to parse appeal_id from callback data")
        return await call.answer("Xatolik: ID topilmadi", show_alert=True)

    feedback = await session.get(StudentFeedback, appeal_id)
    
    if not feedback:
        logger.warning(f"Feedback {appeal_id} not found")
        return await call.answer("Murojaat topilmadi", show_alert=True)
    
    await call.answer("🤖 AI javob tayyorlamoqda...", show_alert=False)
    logger.info(f"Calling AI service for feedback: {feedback.text[:50]}...")
    
    # AI dan javob olish
    suggestion = await generate_reply_suggestion(feedback.text)
    logger.info(f"AI suggestion received: {suggestion[:50]}...")
    
    # Javobni xodimga ko'rsatish
    await call.message.reply(
        f"🤖 <b>AI Taklifi:</b>\n\n"
        f"<i>{suggestion}</i>\n\n"
        f"👆 Nusxalab olib, '✍️ Javob berish' orqali yuborishingiz mumkin.",
        parse_mode="HTML"
    )
    logger.info("AI reply sent successfully")


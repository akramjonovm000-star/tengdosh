from datetime import datetime
import logging
from services.ai_service import analyze_appeal # AI Import


logger = logging.getLogger(__name__)

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TgAccount, Student, StudentFeedback, Staff
from models.states import FeedbackStates
from keyboards.inline_kb import (
    get_student_main_menu_kb,
    get_feedback_anonymity_kb,
    get_rahb_appeal_actions_kb,
    get_student_feedback_menu_kb,
    get_student_feedback_list_kb,
    get_student_feedback_detail_kb,
    get_feedback_recipient_kb,
    get_feedback_cancel_kb,
    get_feedback_rahbariyat_menu_kb,
    get_feedback_dekanat_menu_kb,
    get_staff_appeal_actions_kb,
    get_feedback_confirm_kb, # Added
)
from database.models import StaffRole, TutorGroup, Faculty, UserAppeal
from utils.feedback_utils import get_feedback_thread_text
from services.hemis_service import HemisService
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


# ============================
# Helper — Student olish
# ============================
async def get_student(event, session: AsyncSession):
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == event.from_user.id)
    )
    if tg and tg.student_id:
        return await session.get(Student, tg.student_id)
    return None


# ============================
# 1) Murojaat yuborishni boshlash
# ============================
# ============================
# 1) Murojaatlar menyusi
# ============================
@router.callback_query(F.data.startswith("student_feedback_menu"))
async def feedback_menu(call: CallbackQuery, state: FSMContext):
    logger.info(f"Feedback menu clicked: {call.data} by {call.from_user.id}")
    await call.answer()
    await state.clear()
    
    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"
    
    text = (
        "📨 <b>Murojaatlar bo'limi</b>\n\n"
        "Yangi murojaat yuborishingiz yoki eskilarini kuzatishingiz mumkin."
    )
    kb = get_student_feedback_menu_kb(back_callback=back_to)

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        # Agar oldingi xabar Rasm bo'lsa (Profile) edit_text o'xshamaydi -> O'chirib yangi jo'natamiz
        await call.message.delete()
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    



@router.callback_query(F.data == "student_menu")
async def back_to_main_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await call.answer()
    from handlers.student.navigation import show_student_main_menu
    await show_student_main_menu(call, session, state, text="🏠 <b>Bosh sahifa</b>")


# ============================
# 2) Yangi murojaat (Start)
# ============================
@router.callback_query(F.data == "student_feedback_new")
async def feedback_new(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(FeedbackStates.anonymity_choice)
    try:
        await call.message.edit_text(
            "🕵️‍♂️ <b>Murojaat turini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=get_feedback_anonymity_kb()
        )
    except Exception:
        await call.message.delete()
        await call.message.answer(
            "🕵️‍♂️ <b>Murojaat turini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=get_feedback_anonymity_kb()
        )




# ============================
# 3) Murojaatlar ro'yxati
# ============================
@router.callback_query(F.data == "student_feedback_list")
async def feedback_list(call: CallbackQuery, session: AsyncSession):
    logger.info(f"DEBUG: feedback_list triggered by {call.from_user.id}")
    await call.answer()
    student = await get_student(call, session)
    if not student:
        logger.warning(f"DEBUG: student not found for {call.from_user.id}")
        return await call.answer("Talaba topilmadi", show_alert=True)

    # 50 ta eng oxirgi murojaatni olamiz
    stmt = select(StudentFeedback).where(
        StudentFeedback.student_id == student.id,
        StudentFeedback.parent_id == None  # Faqat root (asosiy) murojaatlarni
    ).order_by(StudentFeedback.updated_at.desc()).limit(50)
    
    result = await session.execute(stmt)
    feedbacks = result.scalars().all()
    logger.info(f"DEBUG: found {len(feedbacks)} feedbacks for student {student.id}")
    
    if not feedbacks:
        await call.answer("Sizda murojaatlar yo'q", show_alert=True)
        return

    try:
        await call.message.edit_text(
            "📂 <b>Sizning murojaatlaringiz:</b>",
            parse_mode="HTML",
            reply_markup=get_student_feedback_list_kb(feedbacks)
        )
    except Exception:
        await call.message.delete()
        await call.message.answer(
            "📂 <b>Sizning murojaatlaringiz:</b>",
            parse_mode="HTML",
            reply_markup=get_student_feedback_list_kb(feedbacks)
        )




# ============================
# 4) Murojaatni ko'rish (Detail)
# ============================
@router.callback_query(F.data.startswith("student_feedback_view:"))
async def feedback_view(call: CallbackQuery, session: AsyncSession):
    await call.answer()
    feedback_id = int(call.data.split(":")[1])
    logger.info(f"Viewing feedback {feedback_id} by {call.from_user.id}")
    
    # Asosiy info va statusni tekshirish uchun
    fb = await session.get(StudentFeedback, feedback_id)
    if not fb:
        return await call.answer("Murojaat topilmadi", show_alert=True)

    # To'liq tarix (Thread)
    thread_text = await get_feedback_thread_text(feedback_id, session)
    
    # Yopilganligini tekshirish (tugmalar uchun)
    is_closed = (fb.status == "closed")

    # Status icon va Text
    status_map = {
        "pending": "⏳ Kutilmoqda",
        "answered": "✅ Javob berilgan",
        "closed": "🔒 Yopilgan",
        "rejected": "❌ Rad etilgan"
    }
    status_text = status_map.get(fb.status, f"⏳ {fb.status}")

    # Role Mapping (Display Name)
    role_map = {
        "dekanat": "Dekanat",
        "tyutor": "Tyutor",
        "buxgalter": "Buxgalteriya",
        "psixolog": "Psixolog",
        "rahbariyat": "Rahbariyat",
        "rector": "Rektor",
        "prorector": "Prorektor",
        "teacher": "O'qituvchi",
        "inspektor": "Inspektor",
        "kafedra": "Kafedra",
        "kafedra_mudiri": "Kafedra mudiri",
        "dekan": "Dekan",
        "dekan_orinbosari": "Dekan o'rinbosari"
    }
    role_key = fb.assigned_role or "unknown"
    role_name = role_map.get(role_key, role_key.capitalize())
    
    date_str = fb.created_at.strftime("%d.%m.%Y %H:%M")

    # Yangi dizayn:
    # 🆔 Murojaat: #123
    # 
    # 📤 Kimga: Dekanat
    # 📅 Qachon: 28.01.2025 12:30
    # 📊 Holati: ⏳ Kutilmoqda
    # ------------
    # Text...

    final_text = (
        f"🆔 <b>Murojaat: #{fb.id}</b>\n\n"
        f"📤 <b>Kimga:</b> {role_name}\n"
        f"📅 <b>Qachon:</b> {date_str}\n"
        f"📊 <b>Holati:</b> {status_text}\n"
        f"------------\n"
        f"{thread_text}"
    )    
    # Agar message juda uzun bo'lsa (4096), qisqartirish kerak.
    if len(final_text) > 4000:
        final_text = final_text[:4000] + "\n...(davomi bor)"

    # Edit message (agar oldingi xabar rasm bo'lsa, edit_caption ishlaydi, text bo'lsa edit_text)
    # Universal yechim: Eski xabarni o'chirib yangisini yozish (clean UI)
    # Agar murojaatda file bo'lsa, media xabar yuboramiz
    if fb.file_id:
        try:
            await call.message.delete()
        except:
            pass
            
        try:
            if fb.file_type == "photo":
                await call.message.answer_photo(
                    fb.file_id,
                    caption=final_text[:1024], # Caption limit
                    parse_mode="HTML",
                    reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed)
                )
            elif fb.file_type == "document":
                await call.message.answer_document(
                    fb.file_id,
                    caption=final_text[:1024],
                    parse_mode="HTML",
                    reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed)
                )
            else:
                await call.message.answer(
                    final_text,
                    parse_mode="HTML",
                    reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed)
                )
        except Exception as e:
            logger.error(f"Error sending feedback media: {e}")
            await call.message.answer(
                final_text,
                parse_mode="HTML",
                reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed)
            )
    else:
        try:
            await call.message.edit_text(
                final_text,
                parse_mode="HTML",
                reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed)
            )
        except Exception:
            await call.message.delete()
            await call.message.answer(
                final_text,
                parse_mode="HTML",
                reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed)
            )




# ============================
# 1.1) Anonimlik tanlandi -> Xabar kuting
# ============================
@router.callback_query(FeedbackStates.anonymity_choice, F.data.startswith("feedback_mode_"))
async def feedback_anonymity_chosen(call: CallbackQuery, state: FSMContext):
    await call.answer()
    is_anon = (call.data == "feedback_mode_anon")
    await state.update_data(is_anonymous=is_anon)

    # Keyingi bosqich: Kimga yuborishni tanlash
    await state.set_state(FeedbackStates.recipient_choice)
    
    try:
        await call.message.edit_text(
            "📩 <b>Murojaat kimga yuborilsin?</b>\n\n"
            "Tegishli bo'limni tanlang:",
            reply_markup=get_feedback_recipient_kb(),
            parse_mode="HTML"
        )
    except Exception:
        await call.message.delete()
        await call.message.answer(
            "📩 <b>Murojaat kimga yuborilsin?</b>\n\n"
            "Tegishli bo'limni tanlang:",
            reply_markup=get_feedback_recipient_kb(),
            parse_mode="HTML"
        )




@router.callback_query(F.data == "student_feedback_recipient")
async def feedback_back_to_main(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "📩 <b>Murojaat kimga yuborilsin?</b>\n\n"
        "Tegishli bo'limni tanlang:",
        reply_markup=get_feedback_recipient_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("fb_menu:"))
async def feedback_menu_nav(call: CallbackQuery):
    await call.answer()
    target = call.data.split(":")[1]
    text = "📩 <b>Murojaat kimga yuborilsin?</b>"
    kb = None
    
    if target == "rahbariyat":
        text = "🏛 <b>Rahbariyatga murojaat</b>\n\nKimga yuborilishi kerakligini tanlang:"
        kb = get_feedback_rahbariyat_menu_kb()
    elif target == "dekanat":
        text = "🏫 <b>Dekanatga murojaat</b>\n\nKimga yuborilishi kerakligini tanlang:"
        kb = get_feedback_dekanat_menu_kb()
        
    if kb:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")



@router.callback_query(F.data.startswith("fb_recipient:"))
async def feedback_recipient_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await call.answer()
    _, role_key = call.data.split(":")
    
    student = await get_student(call, session)
    if not student:
        return await call.answer("Talaba topilmadi", show_alert=True)

    assigned_role = None
    assigned_staff_id = None
    
    # --- 1. FACULTY LEVEL ROLES ---
    faculty_role_map = {
        "dekan": StaffRole.DEKAN,
        "dekan_orinbosari": StaffRole.DEKAN_ORINBOSARI,
        "kafedra": StaffRole.KAFEDRA_MUDIRI,
        "teacher": StaffRole.TEACHER,
        "inspektor": StaffRole.INSPEKTOR,
        "dekanat": StaffRole.DEKANAT # Old legacy
    }

    if role_key in faculty_role_map:
        if role_key == "teacher":
            # --- YANGI LOGIKA: O'qituvchini aniq tanlash ---
            # 1. Hemisdan o'qituvchilar ro'yxatini olamiz
            teachers = []
            if student.hemis_token:
                # Cache orqali schedule dan olish
                teachers = await HemisService.get_semester_teachers(student.hemis_token)
            
            if not teachers:
                 # Fallback: Agar schedule bo'sh bo'lsa yoki token yo'q bo'lsa, eski usul (DB dan random)
                 staff = await session.scalar(
                     select(Staff).where(Staff.faculty_id == student.faculty_id, Staff.role == StaffRole.TEACHER)
                 )
                 if staff:
                     assigned_staff_id = staff.id
                 else:
                     await call.answer("⚠️ Fakultetingizda o'qituvchilar topilmadi.", show_alert=True)
                     return
            else:
                # RO'YXATNI KO'RSATISH
                await state.update_data(assigned_role=StaffRole.TEACHER.value)
                await state.set_state(FeedbackStates.select_teacher)
                
                builder = InlineKeyboardBuilder()
                for t in teachers:
                    t_name = t.get("name", "Noma'lum")
                    t_subj = ", ".join(t.get("subjects", []))
                    if len(t_subj) > 20: t_subj = t_subj[:20] + "..."
                    label = f"{t_name} ({t_subj})" if t_subj else t_name
                    
                    builder.button(text=label, callback_data=f"teacher_sel:{t.get('id')}")
                
                builder.button(text="🔙 Orqaga", callback_data="student_feedback_recipient")
                builder.adjust(1)
                
                await call.message.edit_text(
                    "👨‍🏫 <b>O'qituvchini tanlang:</b>\n"
                    "Sizga dars beradigan o'qituvchilar ro'yxati:",
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
                return 

        else:
            # Boshqa rollar (Dekan, Kafedra mudiri...)
            assigned_role = faculty_role_map[role_key].value
            staff = await session.scalar(
                select(Staff).where(Staff.faculty_id == student.faculty_id, Staff.role == assigned_role)
            )
            if staff:
                assigned_staff_id = staff.id

    # --- 2. UNIVERSITY LEVEL ROLES ---
    elif role_key == "rahbariyat":
        assigned_role = StaffRole.RAHBARIYAT.value
    
    elif role_key == "prorektor":
        assigned_role = StaffRole.PROREKTOR.value

    elif role_key == "yoshlar_prorektor":
        assigned_role = StaffRole.YOSHLAR_PROREKTOR.value

    elif role_key == "rektor":
        assigned_role = StaffRole.REKTOR.value

    # --- 3. SPECIFIC (TYUTOR) ---
    elif role_key == "tyutor":
        # Talabaning guruhiga biriktirilgan tyutorni topish
        tutor_group = await session.scalar(select(TutorGroup).where(TutorGroup.group_number == student.group_number))
        
        if not tutor_group or not tutor_group.tutor_id:
            # return await call.answer("Sizning guruhingizga tyutor biriktirilmagan!", show_alert=True)
            pass
            
        else:
            assigned_staff_id = tutor_group.tutor_id
        
        # Tyutor ID si topilmasa ham, Role=Tyutor qoladi va DB ga tushadi.
        assigned_role = StaffRole.TYUTOR.value

    # --- 4. OTHER (PSIXOLOG) ---
    elif role_key == "psixolog":
        assigned_role = StaffRole.PSIXOLOG.value
        staff = await session.scalar(select(Staff).where(Staff.role == StaffRole.PSIXOLOG))
        if staff:
             assigned_staff_id = staff.id

    # --- 5. BUXGALTERIYA ---
    elif role_key == "buxgalter":
        assigned_role = StaffRole.BUXGALTER.value
        staff = await session.scalar(select(Staff).where(Staff.role == StaffRole.BUXGALTER))
        if staff:
             assigned_staff_id = staff.id

    # --- 6. KUTUBXONA ---
    elif role_key == "kutubxona":
        assigned_role = StaffRole.KUTUBXONA.value
        staff = await session.scalar(select(Staff).where(Staff.role == StaffRole.KUTUBXONA))
        if staff:
             assigned_staff_id = staff.id

    # Check if staff has Telegram Account
    # (Remvoing status note as per user request)
    # if not assigned_staff_id: ...

    await state.update_data(assigned_role=assigned_role, assigned_staff_id=assigned_staff_id)
    await state.set_state(FeedbackStates.waiting_message)
    
    role_names = {
        "rahbariyat": "🏛️ Rahbariyat",
        "prorektor": "👔 O'quv ishlari prorektori",
        "yoshlar_prorektor": "👔 Yoshlar ishlari prorektori",
        "rektor": "🎓 Rektor",
        "dekan": "👤 Dekan",
        "dekan_orinbosari": "👤 Dekan o'rinbosari",
        "kafedra": "🏫 Kafedra mudiri",
        "teacher": "👨‍🏫 Professor-o'qituvchi",
        "inspektor": "🔍 Inspektor",
        "tyutor": "🧑‍🏫 Tyutor",
        "psixolog": "🧠 Psixolog",
        "buxgalter": "💰 Buxgalteriya",
        "kutubxona": "📚 Kutubxona",
        "dekanat": "🏫 Dekanat"
    }

    role_name = role_names.get(role_key, role_key)
    if role_name.startswith("🏛") or role_name.startswith("👔") or role_name.startswith("🎓") or role_name.startswith("👤") or role_name.startswith("🏫") or role_name.startswith("👨") or role_name.startswith("🔍") or role_name.startswith("🧑") or role_name.startswith("🧠") or role_name.startswith("💰") or role_name.startswith("📚"):
        # Strip emoji for clearer sentence
        role_name_clean = role_name.split(" ", 1)[1] if " " in role_name else role_name
    else:
        role_name_clean = role_name

    await call.message.edit_text(
        f"✍️ <b>{role_name_clean}ga murojaatingizni yozing:</b>\n\n"
        "Murojaat matnini kiriting:",
        reply_markup=get_feedback_cancel_kb(),
        parse_mode="HTML"
    )




# ============================
# 2) Matn / media qabul qilish
# ============================
@router.callback_query(FeedbackStates.select_teacher, F.data.startswith("teacher_sel:"))
async def feedback_teacher_selected(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await call.answer()
    hemis_id = int(call.data.split(":")[1])
    
    # Check if staff exists
    staff = await session.scalar(select(Staff).where(Staff.hemis_id == hemis_id))
    
    assigned_staff_id = None
    target_name = "O'qituvchi"
    
    if staff:
        assigned_staff_id = staff.id
        target_name = staff.full_name
    else:
        # Fetch name for UI
        student = await get_student(call, session)
        if student:
             teachers = await HemisService.get_semester_teachers(student.hemis_token)
             t_info = next((t for t in teachers if t["id"] == hemis_id), None)
             if t_info:
                 target_name = t_info["name"]
    
    await state.update_data(
        target_hemis_id=hemis_id,
        assigned_staff_id=assigned_staff_id,
        target_role_name=target_name # Save for UI display
    )
    await state.set_state(FeedbackStates.waiting_message)
    
    # (Removing status note logic)

    await call.message.edit_text(
        f"✍️ <b>{target_name}ga murojaatingizni yozing:</b>\n\n"
        "Murojaat matnini kiriting:",
        reply_markup=get_feedback_cancel_kb(),
        parse_mode="HTML"
    )




@router.message(FeedbackStates.waiting_message)
async def feedback_receive(message: Message, state: FSMContext, session: AsyncSession):
    logger.info(f"feedback_receive: message from {message.from_user.id}, content_type={message.content_type}")
    try:
        # Store message in state, ask for confirmation
        data = await state.get_data()
        role_name = data.get("target_role_name") or "Xodim"
        
        if message.text:
            logger.info(f"feedback_receive: text received: {message.text[:50]}...")
            await state.update_data(feedback_text=message.text)
            await message.answer(
                f"✅ <b>Matn qabul qilindi.</b>\n\n"
                "Endi murojaatingizga <b>Rasm yoki PDF</b> yuklashingiz mumkin (ixtiyoriy).\n"
                "Agar fayl yuklashni xohlamasangiz, <b>'Yuborish'</b> tugmasini bosing.",
                reply_markup=get_feedback_confirm_kb(),
                parse_mode="HTML"
            )
            return

        # Handle Photo
        if message.photo:
            file_id = message.photo[-1].file_id
            logger.info(f"feedback_receive: photo received, file_id={file_id}")
            await state.update_data(file_id=file_id, file_type="photo")
            if message.caption and not data.get("feedback_text"):
                logger.info(f"feedback_receive: photo caption: {message.caption[:50]}...")
                await state.update_data(feedback_text=message.caption)
                
            await message.answer(
                "🖼 <b>Rasm qabul qilindi.</b>\n\n"
                "Murojaatni yuborish uchun <b>'Yuborish'</b> tugmasini bosing yoki matn yuborib uni o'zgartirishingiz mumkin.",
                reply_markup=get_feedback_confirm_kb(),
                parse_mode="HTML"
            )
            return

        # Handle PDF / Document
        if message.document:
            file_id = message.document.file_id
            logger.info(f"feedback_receive: document received, file_id={file_id}")
            await state.update_data(file_id=file_id, file_type="document")
            if message.caption and not data.get("feedback_text"):
                logger.info(f"feedback_receive: doc caption: {message.caption[:50]}...")
                await state.update_data(feedback_text=message.caption)
                
            await message.answer(
                "📄 <b>Hujjat (PDF/Fayl) qabul qilindi.</b>\n\n"
                "Murojaatni yuborish uchun <b>'Yuborish'</b> tugmasini bosing yoki matn yuborib uni o'zgartirishingiz mumkin.",
                reply_markup=get_feedback_confirm_kb(),
                parse_mode="HTML"
            )
            return

        # If no valid type
        logger.warning(f"feedback_receive: invalid content type {message.content_type} from {message.from_user.id}")
        await message.answer(
            "⚠️ Iltimos, murojaat matnini yozing yoki rasm/PDF yuklang.",
            reply_markup=get_feedback_cancel_kb()
        )
    except Exception as e:
        logger.error(f"Error in feedback_receive: {e}", exc_info=True)
        await message.answer("❌ Xatolik yuz berdi. Iltimos qaytadan urining.")


@router.callback_query(F.data == "feedback_send_confirm")
async def feedback_send_confirm(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    logger.info(f"Feedback send confirm clicked by {call.from_user.id}")
    try:
        await call.answer()
        data = await state.get_data()
        logger.info(f"feedback_send_confirm: state_data={data}")
        assigned_role = data.get("assigned_role")
        assigned_staff_id = data.get("assigned_staff_id")
        target_hemis_id = data.get("target_hemis_id")
        text = data.get("feedback_text")
        is_anonymous = data.get("is_anonymous", False)
        file_id = data.get("file_id")
        file_type = data.get("file_type")
        
        if not text and not file_id:
            logger.warning(f"Feedback text missing in state for {call.from_user.id}")
            await call.answer("Xatolik: Matn topilmadi", show_alert=True)
            return

        student = await get_student(call, session)
        if not student:
            logger.warning(f"Student not found for {call.from_user.id}")
            await call.answer("Xatolik: Talaba ma'lumotlari topilmadi", show_alert=True)
            return

        # Create and Save Feedback
        feedback = StudentFeedback(
            student_id=student.id,
            text=text or "[Media]",
            file_id=file_id,
            file_type=file_type,
            status="pending",
            assigned_role=assigned_role,
            assigned_staff_id=assigned_staff_id,
            is_anonymous=is_anonymous,
            # Snapshot data
            student_full_name=student.full_name,
            student_group=student.group_number,
            student_faculty=student.faculty_name,
            student_phone=student.phone
        )
        logger.info(f"Saving feedback for st_id={student.id}")
        session.add(feedback)
        await session.commit()
        logger.info(f"Feedback saved with ID {feedback.id}")

        # Notify Staff (Push)
        if assigned_staff_id:
            logger.info(f"Notifying staff {assigned_staff_id}")
            tg_acc = await session.scalar(select(TgAccount).where(TgAccount.staff_id == assigned_staff_id))
            if tg_acc:
                 try:
                     kb = get_staff_appeal_actions_kb(feedback.id, role=assigned_role, student_id=student.id if not is_anonymous else None)
                     
                     sender_name = "Anonim" if is_anonymous else f"{student.full_name} ({student.group_number})"
                     caption = f"📨 <b>Yangi murojaat!</b>\n\nKimdan: {sender_name}\n\n"
                     if text: caption += f"Matn: {text}"
                     
                     if file_id:
                         if file_type == "photo":
                             await call.bot.send_photo(tg_acc.telegram_id, file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
                         elif file_type == "document":
                             await call.bot.send_document(tg_acc.telegram_id, file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
                         else:
                             await call.bot.send_message(tg_acc.telegram_id, caption, parse_mode="HTML", reply_markup=kb)
                     else:
                         await call.bot.send_message(tg_acc.telegram_id, caption, parse_mode="HTML", reply_markup=kb)
                     logger.info(f"Notification sent to staff tg_id={tg_acc.telegram_id}")
                 except Exception as e:
                     logger.error(f"Failed to send staff notification: {e}")
        
        await state.clear()
        
        msg_text = (
            "✅ <b>Murojaatingiz yuborildi!</b>\n"
            "Javobni 'Yuborilgan murojaatlar' bo'limida kuzatishingiz mumkin."
        )
        kb = get_student_feedback_menu_kb()
        
        try:
            await call.message.edit_text(msg_text, parse_mode="HTML", reply_markup=kb)
        except Exception:
             await call.message.answer(msg_text, parse_mode="HTML", reply_markup=kb)
             
        logger.info(f"Feedback flow completed for {call.from_user.id}")

    except Exception as e:
        logger.error(f"CRITICAL ERROR in feedback_send_confirm: {e}", exc_info=True)
        await call.answer("❌ Xatolik yuz berdi. Iltimos qaytadan urining.", show_alert=True)


# ============================
# 3) Murojaatni yopish
# ============================
@router.callback_query(F.data.startswith("feedback_close:"))
async def feedback_close(call: CallbackQuery, session: AsyncSession):
    await call.answer()
    feedback_id = int(call.data.split(":")[1])
    feedback = await session.get(StudentFeedback, feedback_id)
    
    if feedback:
        feedback.status = "closed"
        await session.commit()
    
    # Xabarni o'zgartirish (tugmalarni olib tashlash)
    current_text = call.message.html_text if hasattr(call.message, "html_text") else call.message.caption or call.message.text
    
    try:
        await call.message.edit_text(
            f"{current_text}\n\n🔒 <b>Murojaat yopildi.</b>",
            parse_mode="HTML",
            reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed=True)
        )
    except Exception:
        await call.message.delete()
        await call.message.answer(
            f"{current_text}\n\n🔒 <b>Murojaat yopildi.</b>",
            parse_mode="HTML",
            reply_markup=get_student_feedback_detail_kb(feedback_id, is_closed=True)
        )



# ============================
# 4) Qayta murojaat (Re-appeal)
# ============================
@router.callback_query(F.data.startswith("feedback_reappeal:"))
async def feedback_reappeal(call: CallbackQuery, state: FSMContext):
    await call.answer()
    feedback_id = int(call.data.split(":")[1])
    await state.update_data(reappeal_feedback_id=feedback_id)
    await state.set_state(FeedbackStates.reappealing)
    
    await call.message.answer(
        "🔄 <b>Qayta murojaat matnini yozing:</b>\n"
        "Xabaringiz to'g'ridan-to'g'ri xodimga yuboriladi.",
        parse_mode="HTML"
    )



# ============================================================
# 8) MOBILE APP UPLOAD HANDLER (FEEDBACK)
# ============================
from database.models import PendingUpload

@router.message(FeedbackStates.WAIT_FOR_APP_FILE, F.photo | F.document | F.video)
async def on_mobile_feedback_upload(message: Message, state: FSMContext, session: AsyncSession):
    student = await get_student(message, session)
    if not student:
        return await message.answer("Siz talaba emassiz.")

    # Find active pending upload for this student
    pending = await session.scalar(
        select(PendingUpload)
        .where(PendingUpload.student_id == student.id, PendingUpload.category == "feedback")
        .order_by(PendingUpload.created_at.desc())
        .limit(1)
    )

    if not pending:
        await state.clear()
        return await message.answer("Hozirda faol murojaat yuklash so'rovi mavjud emas.")

    # Save File ID
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
    else:
        file_id = message.document.file_id
        
    # Update DB
    pending.file_ids = file_id
    await session.commit()
    
    # Notify User
    await message.answer(
        "✅ <b>Fayl qabul qilindi!</b>\n\n"
        "Iltimos, ilovaga qayting va <b>'Yuborish'</b> tugmasini bosing.",
        parse_mode="HTML"
    )
    
    await state.clear()


@router.message(FeedbackStates.reappealing)
async def feedback_reappeal_receive(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    original_feedback_id = data.get("reappeal_feedback_id")
    
    if not original_feedback_id:
        await message.answer("❌ Xatolik: Murojaat ID topilmadi.")
        await state.clear()
        return

    original_feedback = await session.get(StudentFeedback, original_feedback_id)
    
    if not original_feedback:
        await message.answer("❌ Murojaat topilmadi.")
        await state.clear()
        return

    staff_tg = await session.scalar(
        select(TgAccount).where(TgAccount.staff_id == original_feedback.assigned_staff_id)
    )

    target_tg_id = None
    if staff_tg:
        target_tg_id = staff_tg.telegram_id
    else:
        # FALLBACK: Agar aniq xodim topilmasa, o'sha roldagi boshqa xodimni qidiramiz
        fallback_stmt = select(TgAccount).join(Staff).where(Staff.role == original_feedback.assigned_role)
        
        if original_feedback.assigned_role == StaffRole.DEKANAT.value:
            student_chk = await session.get(Student, original_feedback.student_id)
            if student_chk and student_chk.faculty_id:
                fallback_stmt = fallback_stmt.where(Staff.faculty_id == student_chk.faculty_id)
        
        target_tg = await session.scalar(fallback_stmt)
        if target_tg:
            target_tg_id = target_tg.telegram_id
            original_feedback.assigned_staff_id = target_tg.staff_id
            await session.commit()

    try:
        student = await get_student(message, session)
        real_parent_id = original_feedback.parent_id if original_feedback.parent_id else original_feedback.id

        # Yangi feedback yaratish
        new_feedback = StudentFeedback(
            student_id=student.id,
            text=message.text or "Media fayl",
            file_id=message.photo[-1].file_id if message.photo else (message.document.file_id if message.document else None),
            file_type="photo" if message.photo else ("video" if message.video else ("document" if message.document else None)),
            status="reappeal",
            assigned_staff_id=original_feedback.assigned_staff_id,
            assigned_role=original_feedback.assigned_role,
            is_anonymous=original_feedback.is_anonymous,
            parent_id=real_parent_id 
        )
        session.add(new_feedback)
        
        # Asosiy murojaat statusini ham yangilaymiz (Ro'yxatda reappeal sifatida ko'rinishi uchun)
        root_feedback = await session.get(StudentFeedback, real_parent_id)
        if root_feedback:
            root_feedback.status = "reappeal"
            root_feedback.updated_at = datetime.now()
            
        await session.commit()

        # Xodimga yuborish (Faqat agar target_tg_id bo'lsa)
        if target_tg_id:
            history_text = await get_feedback_thread_text(new_feedback.id, session)
            row_kb = get_rahb_appeal_actions_kb(new_feedback.id)

            if new_feedback.file_id:
                if new_feedback.file_type == "photo":
                    await message.bot.send_photo(target_tg_id, new_feedback.file_id, caption=history_text, parse_mode="HTML", reply_markup=row_kb)
                elif new_feedback.file_type == "document":
                    await message.bot.send_document(target_tg_id, new_feedback.file_id, caption=history_text, parse_mode="HTML", reply_markup=row_kb)
                else:
                    await message.bot.send_message(target_tg_id, history_text, parse_mode="HTML", reply_markup=row_kb)
            else:
                await message.bot.send_message(target_tg_id, history_text, parse_mode="HTML", reply_markup=row_kb)

        await message.answer("✅ Murojaatingiz qabul qilindi va mutaxassisga yo'naltirildi.")
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

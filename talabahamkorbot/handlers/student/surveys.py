import logging
import html
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student
from models.states import StudentSurveyStates, StudentAcademicStates
from keyboards.inline_kb import get_student_academic_kb
from services.hemis_service import HemisService
from services.university_service import UniversityService

router = Router()
logger = logging.getLogger(__name__)

def _parse_list(data):
    if data is None: return []
    if isinstance(data, list): return data
    if isinstance(data, dict): return list(data.values())
    return []

@router.callback_query(F.data == "student_surveys")
async def show_surveys_list(call: CallbackQuery, session: AsyncSession):
    account = await session.scalar(
        select(TgAccount)
        .where(TgAccount.telegram_id == call.from_user.id)
        .options(selectinload(TgAccount.student))
    )
    if not account or not account.student or not account.student.hemis_token:
        return await call.answer("❌ HEMIS ma'lumotlari topilmadi", show_alert=True)

    token = account.student.hemis_token
    base_url = UniversityService.get_api_url(account.student.hemis_login)
    await call.answer()
    
    # 1. Fetch from HEMIS
    resp = await HemisService.get_student_surveys(token, base_url=base_url)
    if not resp or not resp.get("success"):
        return await call.message.edit_text(
            "❌ So'rovnomalarni yuklashda xatolik yuz berdi.",
            reply_markup=get_student_academic_kb()
        )

    data = resp.get("data", {})
    not_started = _parse_list(data.get("not_started"))
    in_progress = _parse_list(data.get("in_progress"))
    finished = _parse_list(data.get("finished"))

    msg = "📋 <b>So'rovnomalar</b>\n\n"
    kb_rows = []

    # Faol so'rovnomalar
    active = not_started + in_progress
    if active:
        msg += "<b>🟢 Faol so'rovnomalar:</b>\n"
        for i, s in enumerate(active, 1):
            proj = s.get("quizRuleProjection", {})
            title = proj.get("theme") or s.get("status") or "Nomsiz so'rovnoma"
            sid = proj.get("id") or s.get("id")
            status_text = "Boshlash" if s.get("status") == "Boshlanmagan" else "Davom etish"
            
            msg += f"{i}. {html.escape(title)}\n\n"
            kb_rows.append([InlineKeyboardButton(text=f"🚀 {status_text}: {i}", callback_data=f"survey_start_{sid}")])
    else:
        msg += "<i>Hozircha faol so'rovnomalar yo'q.</i>\n\n"

    # Yakunlangan so'rovnomalar
    if finished:
        msg += "<b>✅ Yakunlangan so'rovnomalar:</b>\n"
        for i, s in enumerate(finished, 1):
            proj = s.get("quizRuleProjection", {})
            title = proj.get("theme") or s.get("status") or "Nomsiz so'rovnoma"
            msg += f"{i}. {html.escape(title)}\n\n"

    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_academic_menu")])
    
    await call.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")

@router.callback_query(F.data.startswith("survey_start_"))
async def start_survey_handler(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    survey_id = call.data.split("_")[-1]
    account = await session.scalar(
        select(TgAccount)
        .where(TgAccount.telegram_id == call.from_user.id)
        .options(selectinload(TgAccount.student))
    )
    token = account.student.hemis_token
    base_url = UniversityService.get_api_url(account.student.hemis_login)
    await call.answer()

    # Load survey details (questions)
    await call.message.edit_text("⏳ So'rovnoma yuklanmoqda...")
    
    resp = await HemisService.start_student_survey(token, survey_id, base_url=base_url)
    if not resp or not resp.get("success"):
        return await call.message.edit_text("❌ So'rovnomani boshlashda xatolik yuz berdi.", reply_markup=get_student_academic_kb())

    data = resp.get("data", {})
    questions = _parse_list(data.get("questions"))
    quiz_rule_id = data.get("quiz_rule_id") or data.get("quiz_info", {}).get("quizRuleProjection", {}).get("id")

    if not questions:
        return await call.message.edit_text("🤷‍♂️ So'rovnomada savollar topilmadi.", reply_markup=get_student_academic_kb())

    # Save to state
    await state.set_state(StudentSurveyStates.taking)
    await state.update_data(
        token=token,
        quiz_rule_id=quiz_rule_id,
        questions=questions,
        current_index=0,
        last_msg_id=call.message.message_id,
        base_url=base_url
    )

    await show_question(call.message, state)

async def show_question(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions")
    idx = data.get("current_index")
    
    if idx >= len(questions):
        # All questions answered (or viewed)
        # Show finish button
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yakunlash", callback_data="survey_finish_confirm")],
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="student_surveys")]
        ])
        return await message.edit_text(
            "🎓 <b>Barcha savollarga javob berdingiz.</b>\n\nNatijalarni saqlash uchun 'Yakunlash' tugmasini bosing.",
            reply_markup=kb,
            parse_mode="HTML"
        )

    q = questions[idx]
    q_id = q.get("id")
    text = q.get("quiz") or "Savol matni yo'q"
    q_type = q.get("buttonType") or "radio"
    variants = _parse_list(q.get("variants"))
    existing_answers = _parse_list(q.get("answers"))

    msg = f"<b>Savol {idx + 1}/{len(questions)}:</b>\n\n"
    msg += f"❓ {html.escape(text)}\n\n"
    
    if existing_answers:
        msg += "<i>Sizning javobingiz: " + ", ".join(existing_answers) + "</i>\n\n"

    kb_rows = []
    if q_type in ["radio", "checkbox"]:
        # Check if any variant is too long for a button
        use_numbered_list = any(len(v) > 34 for v in variants)
        
        if use_numbered_list:
            # 1. Add variants to message text
            msg += "<b>Variantlar:</b>\n\n"
            for v_idx, variant in enumerate(variants, 1):
                msg += f"{v_idx}. {html.escape(variant)}\n\n"
            
            # 2. Create numbered buttons in rows of 5
            temp_row = []
            for v_idx, _ in enumerate(variants):
                temp_row.append(InlineKeyboardButton(text=str(v_idx + 1), callback_data=f"sv_ans_{idx}_{v_idx}"))
                if len(temp_row) == 5:
                    kb_rows.append(temp_row)
                    temp_row = []
            if temp_row:
                kb_rows.append(temp_row)
        else:
            # Short answers: One per row
            for v_idx, variant in enumerate(variants):
                kb_rows.append([InlineKeyboardButton(text=variant, callback_data=f"sv_ans_{idx}_{v_idx}")])
                
    elif q_type == "input":
        msg += "⌨️ <i>Iltimos, javobingizni matn shaklida yozib yuboring:</i>"
    
    kb_rows.append([InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=f"sv_ans_{idx}_skip")])
    kb_rows.append([InlineKeyboardButton(text="❌ To'xtatish", callback_data="student_surveys")])

    # Try to edit last message, if fails (or if we want to move forward from a new message), send new
    try:
        if message.message_id == data.get("last_msg_id"):
            await message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
        else:
            # If we are being called from a text message handler, we might want to edit the LAST bot message
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=data.get("last_msg_id"),
                    text=msg,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
                    parse_mode="HTML"
                )
            except:
                # Fallback: send new message
                new_msg = await message.answer(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
                await state.update_data(last_msg_id=new_msg.message_id)
    except Exception as e:
        logger.error(f"Error in show_question: {e}")
        new_msg = await message.answer(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows), parse_mode="HTML")
        await state.update_data(last_msg_id=new_msg.message_id)

@router.callback_query(StudentSurveyStates.taking, F.data.startswith("sv_ans_"))
async def process_survey_answer(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    idx = int(parts[2])
    v_selector = parts[3]
    
    data = await state.get_data()
    if idx != data.get("current_index"):
        return await call.answer("Eski savol", show_alert=True)

    token = data.get("token")
    questions = data.get("questions")
    q = questions[idx]
    q_id = q.get("id")
    q_type = q.get("buttonType") or "radio"

    await call.answer()
    
    if v_selector != "skip":
        base_url = data.get("base_url")
        # Get actual variant text from index
        try:
            v_idx = int(v_selector)
            variants = _parse_list(q.get("variants"))
            answer = variants[v_idx]
        except (ValueError, IndexError):
            answer = v_selector # fallback
            
        # Submit to HEMIS
        await HemisService.submit_survey_answer(token, q_id, q_type, answer, base_url=base_url)

    # Move to next
    await state.update_data(current_index=idx + 1)
    await show_question(call.message, state)

@router.message(StudentSurveyStates.taking)
async def process_survey_text_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions")
    idx = data.get("current_index")
    
    if idx >= len(questions): return

    q = questions[idx]
    if q.get("buttonType") != "input":
        return await message.answer("Iltimos, yuqoridagi tugmalardan birini tanlang.")

    token = data.get("token")
    base_url = data.get("base_url")
    q_id = q.get("id")
    answer = message.text.strip()
    
    await HemisService.submit_survey_answer(token, q_id, "input", answer, base_url=base_url)
    
    # Move to next
    await state.update_data(current_index=idx + 1)
    
    # Delete user message to keep chat clean
    try:
        await message.delete()
    except: pass

    # Show next question
    await show_question(message, state)

@router.callback_query(StudentSurveyStates.taking, F.data == "survey_finish_confirm")
async def finish_survey_handler(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    token = data.get("token")
    quiz_rule_id = data.get("quiz_rule_id")
    base_url = data.get("base_url")
    
    await call.answer("Yakunlanmoqda...")
    
    success = await HemisService.finish_student_survey(token, quiz_rule_id, base_url=base_url)
    await state.clear()
    
    if success:
        await call.message.edit_text("✅ <b>So'rovnoma muvaffaqiyatli yakunlandi!</b>", reply_markup=get_student_academic_kb(), parse_mode="HTML")
    else:
        await call.message.edit_text("❌ Yakunlashda xatolik yuz berdi, lekin javoblaringiz saqlangan bo'lishi mumkin.", reply_markup=get_student_academic_kb())

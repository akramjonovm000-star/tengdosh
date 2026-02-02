import asyncio
import logging
import html
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, Union
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_connect import AsyncSessionLocal
from database.models import TgAccount, Student, StudentCache, ResourceFile
from models.states import StudentUpdateAuthStates, StudentAcademicStates
from keyboards.inline_kb import get_student_academic_kb
from services.hemis_service import HemisService

router = Router()
logger = logging.getLogger(__name__)

# ============================================================
# 🔐 AUTH HANDLER (MOVED TO TOP)
# ============================================================
@router.message(StudentAcademicStates.waiting_for_password)
async def process_academic_password(message: Message, state: FSMContext, session: AsyncSession):
    password = message.text.strip() if message.text else ""
    if not password: return
    
    # Get Student
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == message.from_user.id).options(selectinload(TgAccount.student)))
    if not account or not account.student:
        await state.clear()
        return await message.answer("Siz talaba sifatida ro‘yxatdan o‘tmagansiz!")
    student = account.student
        
    status_msg = await message.answer("⏳ Tekshirilmoqda...")
    
    # Try Auth
    token, error = await HemisService.authenticate(student.hemis_login, password)
    
    if token:
        # Success
        student.hemis_password = password
        student.hemis_token = token
        await session.commit()
        
        await status_msg.delete()
        await message.answer("✅ <b>Parol yangilandi!</b>", parse_mode="HTML")
        
        # Retrieve Pending Action
        data = await state.get_data()
        pending_action = data.get("pending_action")
        
        await state.clear()
        
        # Route to original destination
        # Note: We pass 'message' instead of 'call'. Handlers must support Message.
        
        if pending_action == "student_attendance":
            await show_attendance(message, session, state)
        elif pending_action == "student_grades":
            await show_grades(message, session, state)
        elif pending_action == "student_rating":
            await show_gpa(message, session, state)
        elif pending_action == "student_subjects":
            await show_subjects_list(message, session, state)
        elif pending_action == "student_schedule":
            await show_schedule(message, session, state)
        elif pending_action == "student_tasks":
            await show_tasks(message, session, state)
            # Fallback
            from handlers.student.navigation import show_student_main_menu
            await show_student_main_menu(message, session, state, text="Bosh menyuga qaytishingiz mumkin.")
            
    else:
        # Add Back Button
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_student_home")]
        ])
        await status_msg.edit_text(
            f"❌ <b>Parol noto'g'ri!</b> ({error or ''})\n\n"
            "Iltimos, qaytadan urinib ko'ring yoki ortga qaytish uchun tugmani bosing:", 
            parse_mode="HTML",
            reply_markup=kb
        )

class GradeStates(StatesGroup):
    waiting_for_password = State()

@router.callback_query(F.data.startswith("subj_res_"))
async def show_subject_resources(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        parts = call.data.split("_")
        subj_id = parts[2]
        sem_code = parts[3] if len(parts) > 3 else "11"
        
        tg_id = call.from_user.id
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student)))
        
        await call.answer()
        if not account or not account.student:
            return await call.message.edit_text("❌ Xatolik", reply_markup=get_student_academic_kb())
            
        token = account.student.hemis_token
        await call.message.edit_text("⏳ Resurslar yuklanmoqda...", reply_markup=None)

        resources = await HemisService.get_student_resources(token, subject_id=subj_id, semester_code=sem_code)
        
        # Back button
        back_btn = InlineKeyboardButton(text="⬅️ Fanlar ro'yxati", callback_data=f"student_resources_menu_{sem_code}")
        
        if not resources:
            return await call.message.edit_text(
                "🤷‍♂️ <b>Bu fan bo'yicha resurslar topilmadi.</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"student_resources_menu_{sem_code}")]]),
                parse_mode="HTML"
            )
            
        msg = "<b>📂 Fan Resurslari</b>\n\n"
        topics_list = []
        for res in resources:
            title = (res.get("title") or "Mavzu nomi yo'q").strip()
            items = res.get("subjectFileResourceItems", [])
            exts = []
            files_count = 0
            for item in items:
                for f in item.get("files", []):
                    files_count += 1
                    ext = f.get("name", "").split(".")[-1].lower() if "." in f.get("name", "") else "fayl"
                    if ext not in exts: exts.append(ext)
            
            topics_list.append({
                "title": title,
                "exts": exts,
                "id": res.get("id"),
                "has_files": files_count > 0
            })

        for i, topic in enumerate(topics_list, 1):
            ext_str = f"({', '.join(topic['exts'])})" if topic['exts'] else ""
            line = f"{i}. 📄 {html.escape(topic['title'])} {ext_str}\n"
            if len(msg) + len(line) < 3800:
                msg += line
            else:
                msg += "... (va boshqalar)"
                break

        kb_list = []
        row = []
        for i, topic in enumerate(topics_list, 1):
            if topic['has_files']:
                # ADDED: _{sem_code}
                row.append(InlineKeyboardButton(text=str(i), callback_data=f"dl_topic_{subj_id}_{topic['id']}_{sem_code}"))
            if len(row) == 5:
                kb_list.append(row)
                row = []
        if row: kb_list.append(row)

        kb_list.append([InlineKeyboardButton(text="📥 Barchasini yuklash", callback_data=f"dl_all_{subj_id}_{sem_code}")])
        kb_list.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"student_subjects_sem_{sem_code}")])

        await call.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="HTML")
        await call.answer()
        
    except Exception as e:
        logger.error(f"Error showing resources: {e}")
        try:
            await call.answer("❌ Xatolik yuz berdi.", show_alert=True)
        except: pass


# ============================================================
# 🏛 AKADEMIK BO'LIM MENYUSI
# ============================================================
@router.callback_query(F.data.in_({"student_academic_menu", "student_academic_menu:profile"}))
async def show_academic_menu(call: CallbackQuery):
    logger.info(f"show_academic_menu reached for user {call.from_user.id}")
    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"

    msg_text = (
        "🏛 <b>Akademik bo'lim</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    kb = get_student_academic_kb(back_callback=back_to)
    
    try:
        await call.message.edit_text(msg_text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to edit_text in academic_menu, trying delete/answer: {e}")
        # Agar rasm bo'lsa edit_text o'xshamaydi -> O'chirib yangi jo'natamiz
        try:
            await call.message.delete()
        except: pass
        await call.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

# ============================================================
# 📊 GPA (Reyting)
# ============================================================
@router.callback_query(F.data == "student_gpa")
async def show_gpa(call: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    logger.info(f"show_gpa reached for user {call.from_user.id}")
    if isinstance(call, CallbackQuery):
        await call.answer()
        user_id = call.from_user.id
    else:
        user_id = call.from_user.id
        
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student)))
    
    if not account or not account.student or not account.student.hemis_token:
        text = "❌ Talaba ma'lumotlari topilmadi."
        try:
            if isinstance(call, CallbackQuery):
                return await call.answer(text, show_alert=True)
            else:
                return await call.answer(text)
        except: return

    token = account.student.hemis_token

    # Auth Check
    auth_status = await HemisService.check_auth_status(token)
    if auth_status == "AUTH_ERROR":
        await state.set_state(StudentAcademicStates.waiting_for_password)
        await state.update_data(pending_action="student_rating")
        
        msg_text = (
            "⚠️ <b>Parolingiz o'zgargan!</b>\n\n"
            "Siz Hemis tizimida parolingizni o'zgartirgansiz.\n"
            "Reyting daftarchasini ko'rish uchun, iltimos, <b>yangi parolni kiriting:</b>"
        )
        try:
            if isinstance(call, CallbackQuery):
                await call.message.edit_text(msg_text, parse_mode="HTML")
            else:
                await call.answer(msg_text, parse_mode="HTML")
        except: pass
        return

    # Loading
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text("⏳ GPA ma'lumotlari yuklanmoqda...", reply_markup=None)
        else:
            msg_target = await call.answer("⏳ GPA ma'lumotlari yuklanmoqda...")
    except: pass

    # Get GPA
    gpa = await HemisService.get_student_performance(token)
    
    msg = (
        f"📊 <b>Reyting Daftarcha (GPA)</b>\n\n"
        f"Sizning o'rtacha o'zlashtirish ko'rsatkichingiz:\n"
        f"⭐ <b>{gpa}</b>\n\n"
        "<i>(Ma'lumotlar joriy semestr asosida olingan)</i>"
    )
    
    # Final Output
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(msg, reply_markup=get_student_academic_kb(), parse_mode="HTML")
        else:
             if 'msg_target' in locals() and isinstance(msg_target, Message):
                 await msg_target.edit_text(msg, reply_markup=get_student_academic_kb(), parse_mode="HTML")
             else:
                 await call.answer(msg, reply_markup=get_student_academic_kb(), parse_mode="HTML")
    except: pass

# ============================================================
# 📈 O'ZLASHTIRISH
# ============================================================
@router.callback_query(F.data.startswith("student_grades"))
async def show_grades(call: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    logger.info(f"show_grades reached for user {call.from_user.id}")
    if isinstance(call, CallbackQuery):
        try:
            await call.answer()
        except Exception as e:
            logger.warning(f"Failed to answer callback (likely expired): {e}")
        user_id = call.from_user.id
        callback_data = call.data
    else:
        user_id = call.from_user.id
        callback_data = "student_grades" # Default if redirected

    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student)))

    if not account or not account.student or not account.student.hemis_token:
        text = "❌ Talaba ma'lumotlari topilmadi."
        try:
           if isinstance(call, CallbackQuery):
               return await call.answer(text, show_alert=True)
           else:
               return await call.answer(text)
        except: return
    
    token = account.student.hemis_token
    
    # 1. Determine requested semester
    requested_sem = None
    if isinstance(call, CallbackQuery) and call.data.startswith("student_grades_sem_"):
        requested_sem = call.data.split("_")[-1]
    
    # Loading
    try:
        loading_text = f"⏳ {int(requested_sem)-10}-semestr baholari yuklanmoqda..." if requested_sem else "⏳ Baholar yuklanmoqda..."
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(loading_text, reply_markup=None)
        else:
            msg_target = await call.answer(loading_text)
    except: pass

    # 2. Token Health Check & Auto-Refresh
    me_data = await HemisService.get_me(token)
    
    if not me_data:
         # Try Auto-Login if credentials exist
         if account.student.hemis_login and account.student.hemis_password:
             # Notify attempting refresh? Maybe silent?
             new_token, err = await HemisService.authenticate(account.student.hemis_login, account.student.hemis_password)
             
             if new_token:
                 account.student.hemis_token = new_token
                 await session.commit()
                 token = new_token
                 me_data = await HemisService.get_me(token)
             else:
                 # Auth Failed -> Ask New Password
                 await state.set_state(StudentAcademicStates.waiting_for_password)
                 await state.update_data(pending_action="student_grades")
                 
                 msg_text = "⚠️ <b>Parolingiz o'zgargan!</b>\n\nIltimos, yangi parolni kiriting:"
                 try:
                     if isinstance(call, CallbackQuery):
                         await call.message.edit_text(msg_text, parse_mode="HTML")
                     else:
                         if 'msg_target' in locals() and isinstance(msg_target, Message):
                             await msg_target.edit_text(msg_text, parse_mode="HTML")
                         else:
                             await call.answer(msg_text, parse_mode="HTML")
                 except: pass
                 return
         else:
             # No creds -> Ask Password (shouldn't happen if registered properly but safe fallback)
             await state.set_state(StudentAcademicStates.waiting_for_password)
             await state.update_data(pending_action="student_grades")
             msg_text = "⚠️ <b>Parol talab qilinadi.</b>\n\nIltimos, parolni kiriting:"
             try:
                  if isinstance(call, CallbackQuery):
                       await call.message.edit_text(msg_text, parse_mode="HTML")
                  else:
                       if 'msg_target' in locals(): await msg_target.edit_text(msg_text, parse_mode="HTML")
                       else: await call.answer(msg_text, parse_mode="HTML")
             except: pass
             return

    # 3. Get current semester code
    current_sem_code = 11
    if me_data:
        sem = me_data.get("semester", {})
        if sem and isinstance(sem, dict):
             current_sem_code = int(sem.get("code") or sem.get("id") or 11)
    
    if not requested_sem:
        requested_sem = str(current_sem_code)

    # 4. Fetch grades
    grades_data = await HemisService.get_student_subject_list(token, semester_code=requested_sem)
    if not grades_data: grades_data = []
    
    # 5. Build message
    msg = f"📊 <b>{int(requested_sem)-10}-semestr baholari</b>\n\n"
    body = format_grades_msg(grades_data)
    msg += body

    # 6. Build Keyboard
    kb_rows = []
    start_sem = 11
    if current_sem_code < 11: current_sem_code = 11
    
    temp_row = []
    for code in range(start_sem, current_sem_code + 1):
        sem_num = code - 10
        btn_text = f"{sem_num}-semestr"
        if str(code) == str(requested_sem):
            btn_text = f"✅ {btn_text}"
            
        temp_row.append(InlineKeyboardButton(text=btn_text, callback_data=f"student_grades_sem_{code}"))
        if len(temp_row) == 2:
            kb_rows.append(temp_row)
            temp_row = []
    if temp_row:
        kb_rows.append(temp_row)
        
    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_academic_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    
    # Final Output
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")
        else:
             if 'msg_target' in locals() and isinstance(msg_target, Message):
                 await msg_target.edit_text(msg, reply_markup=kb, parse_mode="HTML")
             else:
                 await call.answer(msg, reply_markup=kb, parse_mode="HTML")
    except: pass

# ... (Auth handlers remain same) ...

def format_grades_msg(grades_data, web_grades_map=None):
    if web_grades_map is None: web_grades_map = {}
    
    # Calculate Average for this semester
    total_score = 0
    cnt = 0
    for item in grades_data:
        g = item.get("overallScore", {}).get("grade", 0)
        # We assume 0 grade means not graded yet or actually 0
        if g > 0: 
            total_score += g
            cnt += 1
            
    avg_str = ""
    if cnt > 0:
        avg = round(total_score / cnt, 2)
        avg_str = f"⭐️ <b>O'rtacha ball: {avg}</b>\n\n"

    msg = avg_str
    
    for item in grades_data:
        # 1. Subject Name
        subj = "Fan"
        if "curriculumSubject" in item:
             subj = item.get("curriculumSubject", {}).get("subject", {}).get("name", "Fan")
        else:
             subj = item.get("subject", {}).get("name", "Fan")
        
        # 2. Parse Detailed Grades
        details_list = HemisService.parse_grades_detailed(item)
        overall = item.get("overallScore", {}).get("grade", 0)
        
        msg += f"📘 <b>{html.escape(subj)}</b>\n"
        if overall > 0:
            msg += f"   Jami: <b>{overall}</b>\n"
        
        line_parts = []
        for g in details_list:
            t = g['type']
            v = g['val_5']
            # r = g['raw']
            # m = g['max']
            
            if t == 'JN':
                line_parts.append(f"JN: {v}")
            elif t == 'ON':
                line_parts.append(f"ON: {v}")
            elif t == 'YN':
                line_parts.append(f"YN: {v}")
        
        if line_parts:
            msg += "   " + " | ".join(line_parts) + "\n\n"
        else:
            msg += "   <i>Baholar yo'q</i>\n\n"
             
    if len(msg) > 4000: msg = msg[:4000] + "..."
    return msg


@router.callback_query(F.data == "student_tasks")
async def show_tasks(call: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    logger.info(f"show_tasks reached for user {call.from_user.id}")
    if isinstance(call, CallbackQuery):
        await call.answer()
        user_id = call.from_user.id
    else:
        user_id = call.from_user.id
    
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student)))
    
    if not account or not account.student or not account.student.hemis_token:
        text = "❌ Talaba ma'lumotlari topilmadi."
        try:
            if isinstance(call, CallbackQuery):
                return await call.answer(text, show_alert=True)
            else:
                return await call.answer(text)
        except: return

    token = account.student.hemis_token

    # Auth Check
    auth_status = await HemisService.check_auth_status(token)
    if auth_status == "AUTH_ERROR":
        await state.set_state(StudentAcademicStates.waiting_for_password)
        await state.update_data(pending_action="student_tasks")
        
        msg_text = (
            "⚠️ <b>Parolingiz o'zgargan!</b>\n\n"
            "Siz Hemis tizimida parolingizni o'zgartirgansiz.\n"
            "Vazifalarni ko'rish uchun, iltimos, <b>yangi parolni kiriting:</b>"
        )
        try:
            if isinstance(call, CallbackQuery):
                await call.message.edit_text(msg_text, parse_mode="HTML")
            else:
                await call.answer(msg_text, parse_mode="HTML")
        except: pass
        return

    # Normal Logic
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text("⏳ Vazifalar yuklanmoqda...", reply_markup=None)
        else:
            msg_target = await call.answer("⏳ Vazifalar yuklanmoqda...")
    except: pass

    # 1. Get Current Semester
    me_data = await HemisService.get_me(token)
    current_sem_code = "11"
    if me_data:
        sem = me_data.get("semester", {})
        if sem and isinstance(sem, dict):
            current_sem_code = str(sem.get("code") or sem.get("id") or "11")

    # 2. Fetch Subjects for Current Semester
    subjects = await HemisService.get_student_subject_list(token, semester_code=current_sem_code)
    
    if not subjects:
        return await call.message.edit_text(
            "🤷‍♂️ <b>Fanlar topilmadi.</b>\n\nJoriy semestr uchun fanlar biriktirilmagan.",
            reply_markup=get_student_academic_kb(),
            parse_mode="HTML"
        )

    # 3. Build Keyboard with Subjects
    kb_rows = []
    temp_row = []
    
    for item in subjects:
        # Robust parsing similar to show_grades
        if "curriculumSubject" in item:
                subject_info = item.get("curriculumSubject", {})
        else:
                subject_info = item
        
        sub_details = subject_info.get("subject", {})
        name = sub_details.get("name", "Nomsiz fan")
        s_id = sub_details.get("id")
        
        # Use Subject ID for callback
        if s_id:
            temp_row.append(InlineKeyboardButton(text=f"📘 {name}", callback_data=f"tasks_subj_{s_id}_{current_sem_code}"))
        
        if len(temp_row) == 1: # One per row for better readability of long names
                kb_rows.append(temp_row)
                temp_row = []
                
    if temp_row: kb_rows.append(temp_row)
    
    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_academic_menu")])
    
    # Final Output
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(
                "📝 <b>Fanlardan vazifalar</b>\n\n"
                "Vazifalarini ko'rmoqchi bo'lgan fanni tanlang:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
                parse_mode="HTML"
            )
        else:
            if 'msg_target' in locals() and isinstance(msg_target, Message):
                await msg_target.edit_text(
                    "📝 <b>Fanlardan vazifalar</b>\n\n"
                    "Vazifalarini ko'rmoqchi bo'lgan fanni tanlang:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
                    parse_mode="HTML"
                )
            else:
                await call.answer(
                    "📝 <b>Fanlardan vazifalar</b>\n\n"
                    "Vazifalarini ko'rmoqchi bo'lgan fanni tanlang:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
                    parse_mode="HTML"
                )
    except: pass


@router.callback_query(F.data.startswith("tasks_subj_"))
async def show_subject_tasks_detail(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        parts = call.data.split("_")
        subj_id = parts[2]
        sem_code = parts[3] if len(parts) > 3 else "11"
    except:
        return await call.answer("Xatolik", show_alert=True)
        
    tg_id = call.from_user.id
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student)))
    if not account or not account.student: 
        return await call.answer("❌ Talaba ma'lumotlari topilmadi", show_alert=True)

    await call.answer()

    token = account.student.hemis_token
    await call.answer()
    await call.message.edit_text("⏳ Vazifalar tekshirilmoqda...", reply_markup=None)
    
    # 1. Fetch All Tasks for Semester (API requirement: usually fetched by semester, then filtered by subject)
    # Optimization: If HemisService had get_tasks_by_subject, we'd use it. currently get_subject_tasks takes semester.
    # We fetch all tasks for the semester and filter in memory.
    
    all_tasks = await HemisService.get_subject_tasks(token, semester_id=sem_code)
    
    if not all_tasks:
        # Retry logic removed for now / or specific 'empty' handling
        all_tasks = []

    # 2. Filter by Subject ID and Date (Last 7 Days)
    recent_tasks = []
    today = datetime.now()
    cutoff_date = today - timedelta(days=7)
    
    target_subject_name = "" 

    for task in all_tasks:
        # Check Subject
        t_subj = task.get("subject", {})
        t_s_id = str(t_subj.get("id"))
        
        if t_s_id == str(subj_id):
            target_subject_name = t_subj.get("name", "Fan")
            
            # Check Date (deadline or created_at)
            # API response structure varies. Usually 'deadline' is timestamp (sec) or ISO string.
            # Assuming 'deadline' or 'created_at'.
            # debug_tasks.py logic usually shows 'deadline' as timestamp.
            
            ts = task.get("deadline") # Timestamp
            # If no deadline, maybe created_at? 
            # Fallback: if no date is present, we might show it anyway or skip.
            # User request: "oxirgi bir haftada yuklangan vazifa". 
            # Ideally we check 'updated_at' or 'created_at'.
            # If API doesn't give creation date, we can't be 100% sure.
            # Let's assume we show tasks that are RELEVANT (Active).
            # But specific request "oxirgi bir haftada".
            # Let's assume deadline > today-7days is a proxy for "recent/active".
            
            is_recent = False
            if ts:
                 try:
                     d_date = datetime.fromtimestamp(ts)
                     # Using 7 day window logic:
                     # Show if it was assigned recently? Or deadline is near?
                     # Let's simply show ALL Active tasks for now if date logic is ambiguous, 
                     # but try to filter if possible.
                     
                     # Simple logic: If deadline is in future, show it. 
                     # If deadline was in the last 7 days, show it.
                     if d_date > cutoff_date:
                         is_recent = True
                 except: pass
            else:
                 # No date -> Show it just in case
                 is_recent = True
            
            if is_recent:
                recent_tasks.append(task)
    
    # 3. Handle Empty State
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_tasks")]])
    
    if not recent_tasks:
         return await call.message.edit_text(
             f"🤷‍♂️ <b>Bu fandan vazifa berilmagan.</b>\n\n"
             f"<i>(Oxirgi 7 kun ichida yangi vazifa topilmadi)</i>",
             reply_markup=back_kb,
             parse_mode="HTML"
         )
         
    # 4. Show Tasks
    msg = f"📝 <b>{html.escape(target_subject_name)}</b>\n\n"
    
    for i, t in enumerate(recent_tasks, 1):
        name = t.get("name", "Vazifa")
        score = t.get("score", 0)
        max_score = t.get("max_score", 0)
        
        # Deadline formatting
        deadline_str = ""
        ts = t.get("deadline")
        if ts:
             try:
                 d = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
                 deadline_str = f"📅 Muddat: {d}"
             except: pass
        
        status_name = t.get("taskStatus", {}).get("name", "Holat noma'lum")
        
        msg += f"{i}. <b>{name}</b>\n"
        msg += f"   Ball: {score} / {max_score}\n"
        if deadline_str:
            msg += f"   {deadline_str}\n"
        msg += f"   Holati: {status_name}\n\n"
        
    await call.message.edit_text(msg, reply_markup=back_kb, parse_mode="HTML")
@router.callback_query(F.data == "student_attendance")
async def show_attendance(call: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    logger.info(f"show_attendance reached for user {call.from_user.id}")
    msg_target = call if isinstance(call, Message) else call.message
    
    if isinstance(call, CallbackQuery):
        await call.answer()
        user_id = call.from_user.id
    else:
        user_id = call.from_user.id

    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student)))

    if not account or not account.student or not account.student.hemis_token:
        text = "❌ Talaba ma'lumotlari topilmadi."
        try:
            if isinstance(call, CallbackQuery):
                return await call.message.edit_text(text, reply_markup=get_student_academic_kb())
            else:
                return await call.answer(text, reply_markup=get_student_academic_kb())
        except: return

    token = account.student.hemis_token
    
    # Auth Check
    auth_status = await HemisService.check_auth_status(token)
    if auth_status == "AUTH_ERROR":
        await state.set_state(StudentAcademicStates.waiting_for_password)
        await state.update_data(pending_action="student_attendance")
        
        msg_text = (
            "⚠️ <b>Parolingiz o'zgargan!</b>\n\n"
            "Siz Hemis tizimida parolingizni o'zgartirgansiz.\n"
            "Davomatni ko'rish uchun, iltimos, <b>yangi parolni kiriting:</b>"
        )
        try:
            if isinstance(call, CallbackQuery):
                await call.message.edit_text(msg_text, parse_mode="HTML")
            else:
                await call.answer(msg_text, parse_mode="HTML")
        except: pass
        return

    # Normal Logic
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text("⏳ Ma'lumotlar yuklanmoqda...", reply_markup=None)
        else:
            # If message, sending "Loading" is annoying if we edit it later?
            # Or we specifically send a loading message to edit?
            # Since existing logic edits `call.message`, if we passed `msg_target` (User Message), `edit_text` fails.
            # So if Message, we send a NEW message, and use THAT as target?
            # But the subsequent logic uses `call.message.edit_text`.
            # I should create a proxy.
            msg_target = await call.answer("⏳ Ma'lumotlar yuklanmoqda...")
    except: pass

    # Fetch ME to get current semester info
    me_data = await HemisService.get_me(token)
    current_sem_code = 11 # Default
    if me_data and "semester" in me_data:
        try:
            current_sem_code = int(me_data["semester"]["code"])
        except: pass
    
    semesters = []
    start_sem = 11
    if current_sem_code < 11: current_sem_code = 11
    
    for code in range(start_sem, current_sem_code + 1):
        sem_num = code - 10
        semesters.append((f"{sem_num}-semestr", f"attendance_sem_{code}"))
        
    buttons = []
    row = []
    for label, data in semesters:
        row.append(InlineKeyboardButton(text=label, callback_data=data))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_academic_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text_content = (
        "📊 <b>Davomat uchun semestrni tanlang:</b>\n"
        f"<i>Sizning hozirgi semestringiz: {current_sem_code-10}-semestr</i>"
    )
    
    # Final Output
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(text_content, reply_markup=kb, parse_mode="HTML")
        else:
            # Check if we created a loading message
            if 'msg_target' in locals() and isinstance(msg_target, Message) and msg_target.from_user.is_bot:
                 await msg_target.edit_text(text_content, reply_markup=kb, parse_mode="HTML")
            else:
                 await call.answer(text_content, reply_markup=kb, parse_mode="HTML")
    except: pass

@router.callback_query(F.data.startswith("attendance_sem_"))
async def process_attendance_sem(call: CallbackQuery, session: AsyncSession):
    logger.info(f"process_attendance_sem reached for user {call.from_user.id}, data: {call.data}")
    try:
        sem_code = call.data.split("_")[-1]
    except:
        return await call.answer("Xatolik", show_alert=True)
        
    tg_id = call.from_user.id
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student)))
    
    if not account or not account.student:
        return await call.answer("❌ Talaba ma'lumotlari topilmadi", show_alert=True)
        
    await call.answer()
        
    token = account.student.hemis_token
    await call.message.edit_text(f"⏳ {int(sem_code)-10}-semestr davomati yuklanmoqda...", reply_markup=None)
    
    # Fetch Data (Summary + Items) + Caching
    result = await HemisService.get_student_absence(token, semester_code=sem_code, student_id=account.student.id)
    
    total, excused, unexcused, items = 0, 0, 0, []
    if isinstance(result, (tuple, list)):
        if len(result) >= 4:
            total, excused, unexcused, items = result
        elif len(result) >= 3:
            total, excused, unexcused = result[0], result[1], result[2]

    if result is None:
        # Default to empty if error
        total, excused, unexcused, items = 0, 0, 0, []
            
    # Minimalist Summary Header
    msg = (
        f"⏱ <b>Davomat ({int(sem_code)-10}-semestr)</b>\n"
        f"Jami: {total} soat  |  ✅ {excused}  |  ❌ {unexcused}\n"
        f"────────────────\n\n"
    )
    
    if not items:
         msg += "<i>Qoldirilgan darslar yo'q.</i>"
    else:
        # Group by Subject
        grouped = {}
        for item in items:
            subj = item.get("subject", {}).get("name") or "Noma'lum fan"
            ts = item.get("lesson_date")
            
            date_str = "-"
            if ts:
                try:
                    date_str = datetime.fromtimestamp(ts).strftime("%d.%m.%Y")
                except: pass
                
            status = item.get("absent_status", {})
            code = str(status.get("code", "12"))
            s_name = status.get("name", "").lower()
            hour = item.get("hour", 2)
            
            # Minimalist Status
            is_explicable = item.get("explicable", False)
            
            if is_explicable:
                is_excused = True
            else:
                 # Fallback
                 is_excused = (code in ["11", "13"]) or any(x in s_name for x in ["sababli", "kasallik", "ruxsat", "xizmat"])
            
            status_text = "Sababli" if is_excused else "Sababsiz"
            
            if subj not in grouped: grouped[subj] = []
            grouped[subj].append(f"{date_str} ({hour} soat) — {status_text}")

        for subj_name, abs_list in grouped.items():
            pretty_name = subj_name.capitalize()
            msg += f"<b>{pretty_name}</b>\n"
            for rec in abs_list:
                msg += f"  └ {rec}\n"
            msg += "\n"

    if len(msg) > 4000: msg = msg[:4000] + "\n..."
    
    # Back button directly to Semester Selection
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Boshqa semestr", callback_data="student_attendance")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="student_academic_menu")]
    ])
    
    await call.message.edit_text(msg, reply_markup=back_kb, parse_mode="HTML")

# Removed show_attendance_details as it is now merged



@router.callback_query(F.data.startswith("student_resources_menu"))
@router.message(F.text == "📚 Fan resurslari")
async def show_resources_menu(event: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    # 1. Auth Check
    is_msg = isinstance(event, Message)
    tg_id = event.from_user.id
    msg_obj = event if is_msg else event.message
    
    # Check for requested semester in callback
    requested_sem = None
    if not is_msg and event.data.startswith("student_resources_menu_"):
        parts = event.data.split("_")
        if len(parts) > 3:
            requested_sem = parts[3] # student_resources_menu_{sem}

    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student)))
    if not account or not account.student:
        return await msg_obj.answer("Siz talaba sifatida ro‘yxatdan o‘tmagansiz!")
        
    student = account.student
    token = student.hemis_token
    is_auth, error = await HemisService.check_auth_status(token)
    
    if not is_auth:
        await state.update_data(pending_action="student_resources_menu")
        await state.set_state(StudentAcademicStates.waiting_for_password)
        text = f"🔒 <b>Kirish talab etiladi</b>\n\n{error or 'Sessiya vaqti tugagan'}. Parolingizni kiriting:"
        if is_msg:
             await event.answer(text, parse_mode="HTML")
        else:
             await event.message.edit_text(text, parse_mode="HTML", reply_markup=None)
        return

    # 2. Determine Current Semester & Requested Semester
    # Use get_me strategy from show_subjects_list
    current_sem_code = 12 # default fallback
    try:
        me_data = await HemisService.get_me(token)
        if me_data:
            sem = me_data.get("semester", {})
            if sem and isinstance(sem, dict):
                 current_sem_code = int(sem.get("code") or sem.get("id") or 11)
    except: pass
    
    if not requested_sem:
        requested_sem = str(current_sem_code)

    # 3. Fetch Subjects
    if not is_msg: 
        loading_text = f"⏳ {int(requested_sem)-10}-semestr fanlari yuklanmoqda..."
        # Only loading if switching or first load
        try:
             await event.message.edit_text(loading_text, reply_markup=None)
        except: pass
    else: 
        await event.answer("⏳ Fanlar yuklanmoqda...")
    
    try:
        # Fetch Subjects SPECIFICALLY for this semester
        subjects = await HemisService.get_student_subject_list(token, semester_code=requested_sem, student_id=student.id)
        
        # 4. Build Keyboard
        kb_rows = []
        
        if subjects:
             # Sort logic (Robust Name Extraction)
             def get_name(item):
                 if "curriculumSubject" in item:
                     subject_info = item.get("curriculumSubject", {})
                 else:
                     subject_info = item
                 return subject_info.get("subject", {}).get("name") or subject_info.get("name", "")

             subjects.sort(key=get_name)
             
             for i, item in enumerate(subjects, 1):
                # Robust Extraction matching show_subjects_list
                if "curriculumSubject" in item:
                     subject_info = item.get("curriculumSubject", {})
                else:
                     subject_info = item
                     
                sub_details = subject_info.get("subject", {})
                s_name = sub_details.get("name") or subject_info.get("name", "Noma'lum fan")
                s_id = sub_details.get("id") or subject_info.get("id")
                
                if s_id:
                     kb_rows.append([InlineKeyboardButton(text=f"{i}. {s_name}", callback_data=f"subj_res_{s_id}_{requested_sem}")])

        else:
             err_text = f"🤷‍♂️ {int(requested_sem)-10}-semestrda fanlar topilmadi."
             if is_msg: await event.answer(err_text)
             
        # Add Semester Tabs (Range based)
        start_sem = 11
        if current_sem_code < 11: current_sem_code = 11
        sem_row = []
        for code in range(start_sem, current_sem_code + 1):
             sem_num = code - 10
             btn_text = f"{sem_num}-semestr"
             if str(code) == str(requested_sem):
                 btn_text = f"✅ {btn_text}"
             sem_row.append(InlineKeyboardButton(text=btn_text, callback_data=f"student_resources_menu_{code}"))
             
        if sem_row:
             # Split into chunks of 3
             for i in range(0, len(sem_row), 3):
                 kb_rows.append(sem_row[i:i+3])

        kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"student_subjects_sem_{requested_sem}")])
        
        text = f"📚 <b>{int(requested_sem)-10}-semestr fanlari resurslari</b>\n\nQaysi fandan resurslarni yuklamoqchisiz? Tanlang:"
        if not subjects: text = f"⚠️ <b>{int(requested_sem)-10}-semestrda fanlar topilmadi.</b>"
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=kb_rows)
        
        if is_msg:
            await event.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await event.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Resources Menu Error: {e}")
        err_text = "❌ Fanlarni yuklashda xatolik."
        if is_msg: await event.answer(err_text)
        else: await event.message.edit_text(err_text, reply_markup=get_student_academic_kb())

@router.callback_query(F.data.startswith("student_subjects"))
@router.callback_query(F.data.startswith("student_subjects") | F.data.startswith("subjects_sem_"))
async def show_subjects_list(call: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    # 1. Determine requested semester
    requested_sem = None
    if isinstance(call, CallbackQuery):
        if call.data.startswith("student_subjects_sem_"):
            requested_sem = call.data.split("_")[-1]
        elif call.data.startswith("subjects_sem_"):
            requested_sem = call.data.split("_")[-1]

    if isinstance(call, CallbackQuery):
        await call.answer()
        user_id = call.from_user.id
    else:
        user_id = call.from_user.id
        
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student)))
    
    if not account or not account.student or not account.student.hemis_token:
        text = "❌ Talaba ma'lumotlari topilmadi."
        try:
           if isinstance(call, CallbackQuery):
               return await call.answer(text, show_alert=True)
           else:
               return await call.answer(text)
        except: return
        
    token = account.student.hemis_token
    
    # Auth Check
    auth_status = await HemisService.check_auth_status(token)
    if auth_status == "AUTH_ERROR":
        await state.set_state(StudentAcademicStates.waiting_for_password)
        await state.update_data(pending_action="student_subjects")
        
        msg_text = (
            "⚠️ <b>Parolingiz o'zgargan!</b>\n\n"
            "Siz Hemis tizimida parolingizni o'zgartirgansiz.\n"
            "Fanlarni ko'rish uchun, iltimos, <b>yangi parolni kiriting:</b>"
        )
        try:
            if isinstance(call, CallbackQuery):
                await call.message.edit_text(msg_text, parse_mode="HTML")
            else:
                await call.answer(msg_text, parse_mode="HTML")
        except: pass
        return
    
    # 2. Get ME
    me_data = await HemisService.get_me(token)
    current_sem_code = 11
    if me_data:
        sem = me_data.get("semester", {})
        if sem and isinstance(sem, dict):
                current_sem_code = int(sem.get("code") or sem.get("id") or 11)
                
    if not requested_sem:
        requested_sem = str(current_sem_code)

    try:
        loading_txt = f"⏳ {int(requested_sem)-10}-semestr ma'lumotlari yuklanmoqda..."
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(loading_txt, reply_markup=None)
        else:
            msg_target = await call.answer(loading_txt)
    except Exception:
        pass
    
    # 3. Fetch Data concurrently
    student_id = account.student.id
    
    subjects_data, attendance_result, schedule_data = await asyncio.gather(
        HemisService.get_student_subject_list(token, semester_code=requested_sem, student_id=student_id),
        HemisService.get_student_absence(token, semester_code=requested_sem, student_id=student_id),
        HemisService.get_student_schedule_cached(token, semester_code=requested_sem, student_id=student_id)
    )
    
    # Process Attendance
    abs_map = {}
    if isinstance(attendance_result, (tuple, list)) and len(attendance_result) >= 4:
        att_items = attendance_result[3]
        for item in att_items:
            s_name = item.get("subject", {}).get("name")
            if s_name:
                s_name_lower = s_name.lower().strip()
                abs_map[s_name_lower] = abs_map.get(s_name_lower, 0) + item.get("hour", 2)

    # Process Teachers from Schedule
    teacher_map = {}
    if schedule_data:
        for item in schedule_data:
            s_name = item.get("subject", {}).get("name")
            if not s_name: continue
            
            s_name_lower = s_name.lower().strip()
            t_name = item.get("employee", {}).get("name")
            if not t_name: continue
            
            train_type = item.get("trainingType", {}).get("name", "Boshqa")
            
            if s_name_lower not in teacher_map:
                teacher_map[s_name_lower] = {}
            
            label = "Boshqa"
            train_type_l = train_type.lower()
            if "ma'ruza" in train_type_l or "lecture" in train_type_l: label = "Ma'ruza"
            elif "seminar" in train_type_l: label = "Seminar"
            elif "amaliy" in train_type_l or "practice" in train_type_l: label = "Amaliyot"
            elif "laboratoriya" in train_type_l or "laboratory" in train_type_l: label = "Laboratoriya"
            else: label = train_type.capitalize()
            
            if label not in teacher_map[s_name_lower]:
                teacher_map[s_name_lower][label] = set()
            teacher_map[s_name_lower][label].add(t_name)

    if not subjects_data:
        # Build Keyboard even if no subjects (to allow switching semesters)
        kb_rows = []
        start_sem = 11
        if current_sem_code < 11: current_sem_code = 11
        temp_row = []
        for code in range(start_sem, current_sem_code + 1):
            sem_num = code - 10
            btn_text = f"{sem_num}-semestr"
            if str(code) == str(requested_sem): btn_text = f"✅ {btn_text}"
            temp_row.append(InlineKeyboardButton(text=btn_text, callback_data=f"student_subjects_sem_{code}"))
            if len(temp_row) == 2:
                kb_rows.append(temp_row)
                temp_row = []
        if temp_row: kb_rows.append(temp_row)
        kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_academic_menu")])
        
        await call.message.edit_text(
            f"🤷‍♂️ <b>{int(requested_sem)-10}-semestr uchun fanlar topilmadi.</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows),
            parse_mode="HTML"
        )
        return
        
    # 4. Build message
    msg = f"📚 <b>Fanlar ro'yxati ({int(requested_sem)-10}-semestr)</b>\n\n"
    
    for i, item in enumerate(subjects_data, 1):
        if "curriculumSubject" in item:
                subject_info = item.get("curriculumSubject", {})
        else:
                subject_info = item
                
        sub_details = subject_info.get("subject", {})
        name = sub_details.get("name", "Nomsiz fan")
        s_id = sub_details.get("id")
        credit = subject_info.get("credit", 0)
        
        msg += f"<b>{i}. {html.escape(name)}</b> ({credit} kredit)\n"
        
        # Teachers info
        name_lower = name.lower().strip()
        if name_lower in teacher_map:
            tm = teacher_map[name_lower]
            # Order: Seminar -> Amaliyot -> Ma'ruza -> Laboratoriya -> Others
            order = ["Seminar", "Amaliyot", "Ma'ruza", "Laboratoriya"]
            lines = []
            
            # 1. Fixed order items
            for label in order:
                if label in tm:
                    emoji = "👤" if label == "Ma'ruza" else "🧑‍🏫"
                    if label == "Laboratoriya": emoji = "🔬"
                    lines.append(f"   {emoji} {label}: {', '.join(tm[label])}")
            
            # 2. Dynamic/Other types from HEMIS
            for label, teachers in tm.items():
                if label not in order:
                    lines.append(f"   👤 {label}: {', '.join(teachers)}")
            
            if lines:
                msg += "\n".join(lines) + "\n"
                
        # Absence info
        if name_lower in abs_map:
                msg += f"   ❌ Qoldirilgan: {abs_map[name_lower]} soat\n"
                
        msg += "\n"
        
    if len(msg) > 4000: msg = msg[:4000] + "..."
    
    # 5. Build Keyboard
    kb_rows = []
    
    # Semesters
    start_sem = 11
    if current_sem_code < 11: current_sem_code = 11
    temp_row = []
    for code in range(start_sem, current_sem_code + 1):
            sem_num = code - 10
            btn_text = f"{sem_num}-semestr"
            if str(code) == str(requested_sem):
                btn_text = f"✅ {btn_text}"
            temp_row.append(InlineKeyboardButton(text=btn_text, callback_data=f"student_subjects_sem_{code}"))
            if len(temp_row) == 2:
                kb_rows.append(temp_row)
                temp_row = []
    if temp_row:
            kb_rows.append(temp_row)
            
    # Resources (By Subject)
    kb_rows.append([InlineKeyboardButton(text="📂 Fan resurslari", callback_data=f"student_resources_menu_{requested_sem}")])
    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_academic_menu")])
    # Actually resources menu isn't fully separate, usually inside subject.
    # But here we just list subjects. maybe clickable subjects to see resources?
    # Current logic checks callback "subj_res_..." which is from another menu?
    # Let's keep it simple.
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    try:
        if isinstance(call, CallbackQuery):
             await call.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")
        else:
             if 'msg_target' in locals() and isinstance(msg_target, Message):
                  await msg_target.edit_text(msg, reply_markup=kb, parse_mode="HTML")
             else:
                  await call.answer(msg, reply_markup=kb, parse_mode="HTML")
    except: pass




@router.callback_query(F.data.startswith("dl_topic_"))
async def download_single_topic(call: CallbackQuery, session: AsyncSession):
    try:
        parts = call.data.split("_")
        subj_id = parts[2]
        topic_id = parts[3]
        sem_code = parts[4] if len(parts) > 4 else "11" # Extracted sem_code
        
        tg_id = call.from_user.id
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student)))
        if not account or not account.student: return
        token = account.student.hemis_token

        await call.answer("Fayllar tayyorlanmoqda...", show_alert=False)
        
        # Pass sem_code here!
        resources = await HemisService.get_student_resources(token, subject_id=subj_id, semester_code=sem_code)
        target_topic = next((r for r in resources if str(r.get("id")) == str(topic_id)), None)
        
        if not target_topic:
            # Fallback check without semester if failed? No, sem_code should be correct now.
            return await call.message.answer("❌ Mavzu topilmadi (Metadata yangilangan bo'lishi mumkin)")

        # Extract files
        all_files = []
        for item in target_topic.get("subjectFileResourceItems", []):
            for f in item.get("files", []):
                if f.get("url"):
                    all_files.append({"id": item.get("id"), "url": f.get("url"), "name": f.get("name")})

        if not all_files:
            return await call.message.answer("❌ Ushbu mavzuda fayllar yo'q")

        service = HemisService()
        for f_data in all_files:
            f_id = f_data["id"]
            # Cache check
            cached = await session.scalar(select(ResourceFile).where(ResourceFile.hemis_id == f_id))
            if cached and cached.file_id:
                try:
                    await call.message.answer_document(cached.file_id, caption=f_data["name"])
                    continue
                except: pass

            # KEY FIX: Removed invalid 'resource_id' arg
            content, filename = await service.download_resource_file(token, url=f_data["url"])
            if content:
                input_file = BufferedInputFile(content, filename=filename or f_data["name"])
                sent = await call.message.answer_document(input_file, caption=f_data["name"])
                if sent.document and f_id:
                    new_file = ResourceFile(hemis_id=f_id, file_id=sent.document.file_id, 
                                            file_name=filename or f_data["name"], file_type="file")
                    session.add(new_file)
                    await session.commit()
            else:
                await call.message.answer(f"❌ Yuklab bo'lmadi: {f_data['name']}")

    except Exception as e:
        logger.error(f"Download Topic Error: {e}")
        await call.message.answer("❌ Xatolik yuz berdi")

@router.callback_query(F.data.startswith("dl_all_"))
async def download_all_resources(call: CallbackQuery, session: AsyncSession):
    try:
        parts = call.data.split("_")
        subj_id = parts[2]
        sem_code = parts[3] if len(parts) > 3 else "11"
        
        tg_id = call.from_user.id
        account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id).options(selectinload(TgAccount.student)))
        if not account or not account.student: return
        token = account.student.hemis_token

        await call.answer("Barchasini yuklash boshlandi", show_alert=False)
        original_text = call.message.text
        
        resources = await HemisService.get_student_resources(token, subject_id=subj_id, semester_code=sem_code)
        
        # Prepare topics list for status update
        topics_list = []
        for i, res in enumerate(resources, 1):
            title = (res.get("title") or "Nomsiz").strip()
            files = []
            for item in res.get("subjectFileResourceItems", []):
                for f in item.get("files", []):
                    if f.get("url"):
                        files.append({"id": item.get("id"), "url": f.get("url"), "name": f.get("name")})
            topics_list.append({"index": i, "title": title, "files": files, "status": "⏳"})

        total_topics = len(topics_list)
        success_count = 0
        error_count = 0
        
        service = HemisService()
        last_edit_time = 0

        for idx, topic in enumerate(topics_list):
            # Update status in original message
            topic["status"] = "🔄"
            
            # Rebuild text
            updated_msg = "<b>📂 Fan Resurslari (Yuklanmoqda...)</b>\n\n"
            for t in topics_list:
                updated_msg += f"{t['index']}. {t['status']} {html.escape(t['title'])}\n"
            
            # Throttle edits to 1.5s to avoid Flood Limits
            now = asyncio.get_event_loop().time()
            if now - last_edit_time > 1.5 or idx == total_topics - 1:
                try:
                    if len(updated_msg) < 4000:
                        await call.message.edit_text(updated_msg, reply_markup=None, parse_mode="HTML")
                        last_edit_time = now
                except: pass

            topic_success = True
            for f_data in topic["files"]:
                f_id = f_data["id"]
                cached = await session.scalar(select(ResourceFile).where(ResourceFile.hemis_id == f_id))
                
                if cached and cached.file_id:
                    try:
                        await call.message.answer_document(cached.file_id, caption=f_data["name"])
                        continue
                    except: pass

                content, filename = await service.download_resource_file(token, resource_id=f_id, url=f_data["url"])
                if content:
                    input_file = BufferedInputFile(content, filename=filename or f_data["name"])
                    sent = await call.message.answer_document(input_file, caption=f_data["name"])
                    if sent.document and f_id:
                        new_file = ResourceFile(hemis_id=f_id, file_id=sent.document.file_id, 
                                                file_name=filename or f_data["name"], file_type="file")
                        session.add(new_file)
                        await session.commit()
                else:
                    topic_success = False

            if topic_success:
                topic["status"] = "✅"
                success_count += 1
            else:
                topic["status"] = "❌"
                error_count += 1

        # Final Message
        final_msg = "<b>✅ Yuklash yakunlandi!</b>\n\n"
        for t in topics_list:
            final_msg += f"{t['index']}. {t['status']} {html.escape(t['title'])}\n"
        
        final_msg += f"\nJami mavzular: {total_topics}\nMuvaffaqiyatli: {success_count}\nXatolik: {error_count}"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Fanlar ro'yxati", callback_data=f"student_subjects_sem_{sem_code}")]
        ])
        
        try:
            await call.message.edit_text(final_msg[:4000], reply_markup=kb, parse_mode="HTML")
        except:
            await call.message.answer(final_msg[:4000], reply_markup=kb, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Download All Error: {e}")
        await call.message.answer("❌ Xatolik yuz berdi.")

# ============================================================
# 📅 DARS JADVALI
# ============================================================
@router.callback_query(F.data == "student_schedule")
async def show_schedule(call: Union[CallbackQuery, Message], session: AsyncSession, state: FSMContext):
    logger.info(f"show_schedule reached for user {call.from_user.id}")
    if isinstance(call, CallbackQuery):
        await call.answer()
        user_id = call.from_user.id
    else:
        user_id = call.from_user.id
        
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == user_id).options(selectinload(TgAccount.student)))

    if not account or not account.student or not account.student.hemis_token:
        text = "❌ Talaba ma'lumotlari topilmadi."
        try:
           if isinstance(call, CallbackQuery):
               return await call.answer(text, show_alert=True)
           else:
               return await call.answer(text)
        except: return

    token = account.student.hemis_token
    
    # Auth Check
    auth_status = await HemisService.check_auth_status(token)
    if auth_status == "AUTH_ERROR":
        await state.set_state(StudentAcademicStates.waiting_for_password)
        await state.update_data(pending_action="student_schedule")
        
        msg_text = (
            "⚠️ <b>Parolingiz o'zgargan!</b>\n\n"
            "Siz Hemis tizimida parolingizni o'zgartirgansiz.\n"
            "Dars jadvalini ko'rish uchun, iltimos, <b>yangi parolni kiriting:</b>"
        )
        try:
            if isinstance(call, CallbackQuery):
                await call.message.edit_text(msg_text, parse_mode="HTML")
            else:
                await call.answer(msg_text, parse_mode="HTML")
        except: pass
        return
    
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text("⏳ Dars jadvali yuklanmoqda...", reply_markup=None)
        else:
            msg_target = await call.answer("⏳ Dars jadvali yuklanmoqda...")
    except: pass

    today = datetime.now()
    weekday = today.weekday()
    
    # User request: On Sunday (weekday 6), show NEXT week. 
    # Otherwise show CURRENT week.
    if weekday == 6:
        # Advance to next Monday
        start_week = today + timedelta(days=1)
    else:
        # Go back to current Monday
        start_week = today - timedelta(days=weekday)
    
    # Ensure start_week is at 00:00:00
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_week = start_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    s_date = start_week.strftime("%Y-%m-%d")
    e_date = end_week.strftime("%Y-%m-%d")

    # Fetch
    try:
        raw_schedule = await HemisService.get_student_schedule(token, week_start=s_date, week_end=e_date)
        # Strict Filtering: Ensure lessons strictly fall within the 7-day range
        # (HEMIS API sometimes returns data outside the requested range)
        start_ts = start_week.timestamp()
        end_ts = end_week.timestamp()
        
        # Rebuild the list with strict timestamp filtering
        schedule_data = [
            item for item in raw_schedule 
            if item.get("lesson_date") and start_ts <= item.get("lesson_date") <= end_ts
        ]
    except Exception as e:
        logger.error(f"Schedule fetch error: {e}")
        schedule_data = []
    
    if not schedule_data:
         text = f"📅 <b>Dars jadvali</b>\n\n({s_date} — {e_date})\n\nUshbu hafta uchun darslar topilmadi."
         try:
             if isinstance(call, CallbackQuery):
                 await call.message.edit_text(text, reply_markup=get_student_academic_kb(), parse_mode="HTML")
             else:
                 if 'msg_target' in locals() and isinstance(msg_target, Message):
                     await msg_target.edit_text(text, reply_markup=get_student_academic_kb(), parse_mode="HTML")
                 else:
                     await call.answer(text, reply_markup=get_student_academic_kb(), parse_mode="HTML")
         except: pass
         return
    
    # Group by ISO Date String (YYYY-MM-DD)
    grouped = {}
    
    for item in schedule_data: 
        date_ts = item.get("lesson_date") 
        if not date_ts: continue
        
        try:
             d_obj = datetime.fromtimestamp(date_ts)
             iso_date = d_obj.strftime("%Y-%m-%d")
        except:
             continue # Skip invalid dates
             
        if iso_date not in grouped: grouped[iso_date] = []
        
        # Parse fields
        subj_data = item.get("subject", {})
        subj = subj_data.get("name", "Noma'lum").upper()
        
        audit_data = item.get("auditorium", {})
        audit = audit_data.get("name", "Xona yo'q")
        
        type_data = item.get("trainingType", {})
        type_name = type_data.get("name", "Dars")
        
        emp_data = item.get("employee", {})
        teacher = emp_data.get("name", "O'qituvchi yo'q")
        
        pair = item.get("lessonPair", {})
        time_s = pair.get("start_time", "")
        # number = pair.get("code", "") 
        pair_code = str(pair.get("code", ""))
        # Fix: 11 -> 1, 12 -> 2 logic
        if len(pair_code) == 2 and pair_code.startswith("1") and pair_code[1].isdigit():
             pair_code = pair_code[1:]
        
        line = f"<b>{pair_code}. {html.escape(subj)}</b>\n"
        line += f"   🏫 {audit} | 📋 {type_name} | 👨‍🏫 {teacher}\n"
        line += f"   ⏰ <b>{time_s}</b>"
        
        grouped[iso_date].append((time_s, line))

    text = f"📅 <b>Dars Jadvali</b>\n({s_date} — {e_date})\n\n"
    
    for iso_date in sorted(grouped.keys()):
        lessons_list = grouped[iso_date]
        lessons_list.sort(key=lambda x: x[0])
        
        # Format Header
        try:
            d_obj = datetime.strptime(iso_date, "%Y-%m-%d")
            days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
            day_name = days[d_obj.weekday()]
            pretty_date = f"{day_name}, {d_obj.strftime('%d.%m.%Y')}"
        except:
            pretty_date = iso_date

        text += f"🗓 <b>{pretty_date}</b>\n\n"
        for _, l_text in lessons_list:
             text += f"{l_text}\n\n"
        text += "➖➖➖➖➖➖➖➖➖➖\n\n"
        
    if len(text) > 4000: text = text[:4000] + "..."
    
    try:
        if isinstance(call, CallbackQuery):
            await call.message.edit_text(text, reply_markup=get_student_academic_kb(), parse_mode="HTML")
        else:
             if 'msg_target' in locals() and isinstance(msg_target, Message):
                 await msg_target.edit_text(text, reply_markup=get_student_academic_kb(), parse_mode="HTML")
             else:
                 await call.answer(text, reply_markup=get_student_academic_kb(), parse_mode="HTML")
    except: pass

# ============================================================
# 📝 FANLARDAN VAZIFALAR
# ============================================================
# Duplicate student_tasks handler removed

# ============================================================
# ⬅️ ORTGA
# ============================================================
@router.callback_query(F.data == "go_student_home")
async def go_home(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    # This handler is a duplicate of navigation.py, but we'll make it consistent
    # Or we could just remove it if navigation_router is registered before academic_router
    from handlers.student.navigation import show_student_main_menu
    await show_student_main_menu(call, session, state)
    await call.answer()






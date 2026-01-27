
import os
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import TgAccount, StaffRole, Staff, Student
from services.ai_service import generate_answer_by_key, summarize_konspekt
from utils.document_parser import extract_text_from_file
from models.states import AIStates
from utils.student_utils import get_student_by_tg, check_premium_access
from services.grant_service import calculate_grant_score
from services.hemis_service import HemisService

router = Router()
logger = logging.getLogger(__name__)

# ============================================================
# 1. AI BOSHMENYU (Role bo'yicha)
# ============================================================
@router.callback_query(F.data == "ai_assistant_main")
async def cb_ai_main(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear() # Reset any previous states
    
    tg_id = call.from_user.id
    acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
    
    if not acc:
        return await call.answer("Hisob topilmadi", show_alert=True)
        
    role = acc.current_role
    
    # PREMIUM CHECK
    allowed, text, _ = await check_premium_access(tg_id, session, "AI Yordamchi")
    if not allowed:
        return await call.answer(text, show_alert=True)

    # Back button logic
    back_cb = "go_home"
    if role == "student":
        back_cb = "go_student_home"
    elif role == StaffRole.OWNER.value:
        back_cb = "owner_menu"
    elif role == StaffRole.RAHBARIYAT.value:
        back_cb = "rahb_menu"
    elif role == StaffRole.DEKANAT.value:
        back_cb = "dek_menu"
    elif role == StaffRole.TYUTOR.value:
        back_cb = "tutor_menu"
    elif role == StaffRole.YOSHLAR_YETAKCHISI.value:
        back_cb = "yetakchi_broadcast_menu" # Fallback, usually they have their own menu
        
    keyboard_rows = []
    
    # ------------------ STUDENT PROMPTS ------------------
    if role == "student" or role == StaffRole.KLUB_RAHBARI.value:
        keyboard_rows.append([InlineKeyboardButton(text="📏 Kredit-modul tizimi", callback_data="ai_ask:credit_system")])
        # KONSPEKT
        keyboard_rows.append([InlineKeyboardButton(text="📝 Konspekt qilish (File/Matn)", callback_data="ai_konspekt_start")])
        # GRANT CALCULATOR
        keyboard_rows.append([InlineKeyboardButton(text="🎓 Grant taqsimoti", callback_data="ai_grant_calc")])
        
    # ------------------ TYUTOR PROMPTS ------------------
    elif role == StaffRole.TYUTOR.value:
        keyboard_rows.append([InlineKeyboardButton(text="🧠 Psixologik yondashuv", callback_data="ai_ask:student_psychology")])
        keyboard_rows.append([InlineKeyboardButton(text="📋 Faollikni baholash", callback_data="ai_ask:activity_grading")])
        # Common staff prompts
        keyboard_rows.append([InlineKeyboardButton(text="📝 Mehnat ta'tili", callback_data="ai_ask:labor_laws")])
        keyboard_rows.append([InlineKeyboardButton(text="💼 KPI tizimi", callback_data="ai_ask:kpi_system")])

    # ------------------ STAFF (Rahbariyat/Dekanat/Owner) PROMPTS ------------------
    else:
        keyboard_rows.append([InlineKeyboardButton(text="📝 Mehnat ta'tili qoidalari", callback_data="ai_ask:labor_laws")])
        keyboard_rows.append([InlineKeyboardButton(text="💼 KPI tizimi", callback_data="ai_ask:kpi_system")])

    # Footer
    keyboard_rows.append([InlineKeyboardButton(text="💬 AI bilan suhbat", callback_data="ai_start_free_chat")]) # NEW
    keyboard_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_cb)])
    
    await call.message.edit_text(
        "🤖 <b>AI Yordamchi</b>\n\n"
        "Sizga qanday yordam bera olaman? Quyidagi mavzulardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows),
        parse_mode="HTML"
    )
    await call.answer()


# ============================================================
# 2. SAVOL-JAVOB TUGMALARI (Tez orada...)
# ============================================================
@router.callback_query(F.data.startswith("ai_ask:"))
async def cb_ai_ask(call: CallbackQuery):
    logger.info(f"AI ASK Triggered: {call.data}")
    await call.answer()
    
    try:
        topic_key = call.data.split(":")[1]
        
        if topic_key == "credit_system":
            await call.message.edit_text("⏳ <b>AI ma'lumot tayyorlamoqda...</b>\n\nKredit-modul tizimi bo'yicha eng muhim ma'lumotlar yozilmoqda.", parse_mode="HTML")
            
            prompt = """
            ROLE:
            You are an AI assistant inside a student app.
            Your task is to explain the Credit-Module System clearly and simply ONLY for students.

            LANGUAGE:
            Uzbek (oddiy, tushunarli, talabalar tili), Kirill yoki Lotin (Lotin afzal).

            STYLE RULES:
            - Juda sodda yoz
            - Qonun bandlari va rasmiy atamalarni keltirma
            - Murakkab jumla ishlatma
            - Har bir fikr aniq va qisqa bo‘lsin
            - Savol tug‘diradigan joy qoldirma
            - "Talaba nimani bilishi kerak?" degan nuqtadan yoz

            📌 WHAT TO EXPLAIN (majburiy):
            - Kredit-modul tizimi nima ekanligi (Oddiy tilda)
            - Kredit nimani anglatadi (O'lchov birligi)
            - Modul nima ekanligi (Fanlar bloki)
            - Kredit qanday hisoblanadi:
              * 1 kredit = 25–30 soat (Auditoriya + Mustaqil ta'lim)
            - Semestr va yillik kreditlar:
              * 1 semestr = 30 kredit
              * 1 yil = 60 kredit
              * Bakalavr = 240 kredit
              * Magistr = 120 kredit
            - Talabaning vazifalari:
              * Fan tanlash
              * Kredit yig‘ish
              * Mustaqil o‘qish
            - Baholash tizimi:
              * Reyting asosida (5 baxo yo'q, 100 ballik tizim)
              * GPA nima ekanligi (O'rtacha ball)
              * GPA nimaga ta’sir qilishi (Stipendiya, Magistratura)
            - Fan yiqilsa nima bo‘ladi:
              * Kredit berilmaydi
              * Yozgi semestrda qayta o‘qish (pullik)
            - Kreditlar nimaga kerak:
              * Bitiruv diplomi uchun
              * O'qishni ko'chirish (Perevod)
              * Xorijda o‘qish (Akademik mobillik)

            Talaba uchun eng muhim qoidalar:
            - Kredit yig‘ilmasa — diplom yo'q
            - Bahodan ko‘ra kredit soni muhim
            - Mustaqil o‘qish majburiy

            🚫 WHAT NOT TO DO:
            - Qonun nomlari yoki bandlarini yozma
            - "VM qarori", "Nizomga asosan" kabi iboralarni ishlatma
            - Ortiqcha izoh yoki falsafa qilma

            🎯 OUTPUT FORMAT:
            - Sarlavhalar bilan yoz
            - Punktlar bilan tushuntir (Bullet points)
            - Qisqa va tiniq matn bo‘lsin
            - Emojilarni ishlat
            
            MANBA (O'rganish uchun): https://lex.uz/ru/docs/-5193564
            (Lekin javobda manbani ko'rsatish shart emas, faqat mazmunini ol).
            
            Javobni O'zbek tilida (Lotin), quyidagi FORMATLASH QOIDALARIGA qat'iy rioya qilgan holda yoz:
            
            ⚠️ TELEGRAM HTML QOIDALARI (BU JUDA MUHIM):
            1. MUMKIN EMAS (Telegramda ishlamaydi):
            - <h1>, <h2>, <h3>... (Sarlavhalar uchun shunchaki <b>Qalin Matn</b> ishlat)
            - <ul>, <ol>, <li> (Ro'yxatlar uchun "-", "•" yoki "1." kabi belgilarni qo'lda yoz)
            - <p>, <br> (Yangi qator uchun shunchaki \n ishlat)
            - Markdown (**, __) ISHLATMA.
            
            2. RUXSAT BERILGAN:
            - <b>Qalin matn</b>
            - <i>Kursiv</i>
            - <u>Tagiga chizilgan</u>
            - <s>O'chirilgan</s>
            - <a href='URL'>Link</a>
            - <code>Kod</code>
            
            Javobni faqat ruxsat berilgan HTML teglar bilan bezat. Har bir bo'limni <b>Sarlavha</b> ko'rinishida ajrat.
            """
            
            answer = await generate_answer_by_key("credit_system", prompt)
            
            if not answer:
                 answer = "❌ Ma'lumot olishda xatolik."

            # Basic cleanup for unsupported tags
            answer = answer.replace("<h1>", "<b>").replace("</h1>", "</b>")
            answer = answer.replace("<h2>", "<b>").replace("</h2>", "</b>")
            answer = answer.replace("<h3>", "<b>").replace("</h3>", "</b>")

            await call.message.edit_text(
                answer,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="ai_assistant_main")]
                ])
            )
    except Exception as e:
        logger.error(f"Credit System AI Error: {e}")
        await call.message.edit_text(
            f"❌ <b>Xatolik yuz berdi:</b>\n{str(e)}\n\nIltimos admin bilan bog'laning.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="ai_assistant_main")]
            ]),
            parse_mode="HTML"
        )
        return

    # User request: "Bular ishga tushmagunicha tez orada deb tursin"
    await call.answer("🛠 Bu bo'lim tez orada ishga tushadi!", show_alert=True)


# ============================================================
# 3. ERKIN SUHBAT (Free Chat)
# ============================================================
@router.callback_query(F.data == "ai_start_free_chat")
async def cb_start_free_chat(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    # PREMIUM CHECK
    allowed, text, _ = await check_premium_access(call.from_user.id, session, "AI Chat")
    if not allowed:
        return await call.answer(text, show_alert=True)
        
    await state.set_state(AIStates.chatting)
    
    # Get Name
    tg_id = call.from_user.id
    acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
    name = "Talaba"
    
    if acc and acc.current_role == "student" and acc.student_id:
        student = await session.get(Student, acc.student_id)
        if student:
            # Name check and auto-fix
            # Force update if name is missing OR generic "Talaba"
            # Note: We can implicitly check if token is valid by trying get_me
            if not student.full_name or student.full_name == "Talaba":
                from services.hemis_service import HemisService
                
                # Check token validity / fetch name
                if student.hemis_token:
                     me_data = await HemisService.get_me(student.hemis_token)
                     
                     # If 401 (None returned or error), try refreshing if password exists
                     if not me_data and student.hemis_login and student.hemis_password:
                         logger.info(f"Token expired for {student.id}, attempting refresh...")
                         new_token, err = await HemisService.authenticate(student.hemis_login, student.hemis_password)
                         if new_token:
                             student.hemis_token = new_token
                             await session.commit()
                             # Retry get_me
                             me_data = await HemisService.get_me(new_token)
                             logger.info("Token refreshed successfully.")
                         else:
                             logger.error(f"Auto-refresh failed for {student.id}: {err}")

                     if me_data:
                         # Construct full name safely
                         f_name_parts = [
                             me_data.get('firstname', ''), 
                             me_data.get('lastname', ''), 
                             me_data.get('fathername', '')
                         ]
                         f_name = " ".join(filter(None, f_name_parts)).strip()
                         
                         if f_name:
                             student.full_name = f_name
                             await session.commit()
            
            if student.full_name:
                parts = student.full_name.split()
                if len(parts) >= 2:
                     name = f"{parts[1]}" if len(parts) > 1 else parts[0]
                else:
                     name = student.full_name

    await call.message.edit_text(
        f"🤖 <b>Salom, {name}!</b>\n\n"
        "Men sizning shaxsiy AI yordamchingizman. Sizga o'qish, baholar va boshqa masalalarda yordam bera olaman.\n\n"
        "Menga istalgan savolingizni yozing 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Suhbatni tugatish", callback_data="ai_assistant_main")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()

from services.ai_service import generate_response

from datetime import datetime, timedelta
from services.context_builder import build_student_context

@router.message(AIStates.chatting)
async def process_chat_message(message: Message, session: AsyncSession, state: FSMContext):
    if not message.text:
        return

    allowed, _, _ = await check_premium_access(message.from_user.id, session)
    if not allowed:
        await state.clear()
        return await message.answer("⚠️ Premium muddati tugagan yoki ruxsat yo'q. Suhbatni davom ettirish uchun obunani yangilang.")
        
    wait_msg = await message.answer("🤔 O'ylayapman...")
    
    # 1. Talaba kontekstini aniqlash
    tg_id = message.from_user.id
    acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
    
    prompt_text = message.text
    
    if acc and acc.current_role == "student" and acc.student_id:
        student = await session.get(Student, acc.student_id)
        if student:
            # Context yangilash kerakmi? (Agar yo'q bo'lsa yoki eski bo'lsa)
            # User "tizimga kirishi bilan" dedi, bu yerda "chatga kirishi bilan" deb tushunamiz.
            # Va 24 soatlik limitni tekshiramiz.
            need_update = False
            if not student.ai_context:
                need_update = True
            elif student.last_context_update:
                if datetime.utcnow() - student.last_context_update > timedelta(hours=24):
                    need_update = True
            
            context_str = student.ai_context
            if need_update:
                 # Real-time update (Nightly job also does this, but this is fallback/lazy-load)
                 context_str = await build_student_context(session, student.id)
            
            # CHECK FOR CUSTOM CONTEXT (e.g. Grant Calc history)
            data = await state.get_data()
            custom_ctx = data.get("custom_context")
            
            if custom_ctx:
                 # Use the session-specific context
                 prompt_text = f"CONTEXT:\n{custom_ctx}\n\nUSER_QUERY:\n{message.text}"
            elif context_str:
                # System prompt injection technique
                prompt_text = f"STUDENT_CONTEXT:\n{context_str}\n\nUSER_QUERY:\n{message.text}"

    response = await generate_response(prompt_text)
    
    # 2. Log yozish (Analytics)
    if acc and acc.current_role == "student" and acc.student_id:
        # Student object may be loaded above, if not load it
        if 'student' not in locals() or not student:
            student = await session.get(Student, acc.student_id)
            
        if student:
            from database.models import StudentAILog # Import here to avoid circular or top-level mess
            
            log_entry = StudentAILog(
                student_id=student.id,
                full_name=student.full_name,
                university_name=student.university_name,
                faculty_name=student.faculty_name,
                group_number=student.group_number,
                user_query=message.text, # Original user text, not prompt
                ai_response=response
            )
            session.add(log_entry)
            await session.commit()

    await wait_msg.delete()
    
    await message.answer(
        response,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Suhbatni tugatish", callback_data="ai_assistant_main")]
        ])
    )


# ============================================================
# 4. KONSPEKT QILISH FUNKSIYASI
# ============================================================
@router.callback_query(F.data == "ai_konspekt_start")
async def cb_konspekt_start(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    allowed, text, _ = await check_premium_access(call.from_user.id, session, "AI Konspekt")
    if not allowed:
        return await call.answer(text, show_alert=True)
        
    await state.set_state(AIStates.waiting_for_konspekt)
    
    msg_text = (
        "📚 <b>Konspekt Yordamchisi</b>\n\n"
        "Men sizga uzun ma'ruza matnlari yoki taqdimotlardan eng muhim joylarini ajratib olishga yordam beraman.\n\n"
        "📎 <b>Nima qilishingiz kerak?</b>\n"
        "Menga <b>Word (DOCX)</b>, <b>PowerPoint (PPTX)</b>, <b>PDF</b> fayl yoki shunchaki <b>uzun matn</b> yuboring.\n\n"
        "Men uni tahlil qilib, daftarga yozish uchun qulay, qisqa va lo'nda <b>konspekt</b> tayyorlab beraman.\n\n"
        "👇 <i>Marhamat, faylni yoki matnni shu yerga tashlang:</i>"
    )
    
    await call.message.edit_text(
        msg_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="ai_assistant_main")]
        ]),
        parse_mode="HTML"
    )
    await call.answer()


@router.message(AIStates.waiting_for_konspekt)
async def msg_process_konspekt(message: Message, state: FSMContext, bot: Bot):
    
    processing_msg = await message.answer("⏳ <i>Fayl o'qilmoqda va tahlil qilinmoqda...</i>", parse_mode="HTML")
    
    text_content = ""
    
    try:
        # A) Matn yuborilganda
        if message.text:
            text_content = message.text
            
        # B) Fayl yuborilganda (Document)
        elif message.document:
            import io
            from utils.document_parser import extract_text_from_stream
            
            file_id = message.document.file_id
            file_name = message.document.file_name
            
            # Download to Memory
            file_stream = io.BytesIO()
            await bot.download(message.document, destination=file_stream)
            
            # Extract text from stream
            ext = file_name.split(".")[-1]
            text_content = extract_text_from_stream(file_stream, ext)
            
            # No cleanup needed as it's in RAM
                
        else:
            await processing_msg.edit_text("❌ Iltimos, fayl yoki matn yuboring.")
            return

        # Check if text was extracted
        if not text_content or len(text_content.strip()) < 10:
            await processing_msg.edit_text("⚠️ Fayldan matn o'qib bo'lmadi yoki matn juda qisqa.")
            return

        # AI Summary
        await processing_msg.edit_text("🤖 <i>AI konspekt yozmoqda...</i>", parse_mode="HTML")
        summary = await summarize_konspekt(text_content)
        
        # Send result
        # Agar javob juda uzun bo'lsa
        if len(summary) > 4000:
            parts = [summary[i:i+4000] for i in range(0, len(summary), 4000)]
            for part in parts:
                await message.answer(part, parse_mode="Markdown")
        else:
            await message.answer(summary, parse_mode="Markdown")
            
        # Error check
        if summary.startswith("⚠️") or "xatolik" in summary.lower():
            await state.clear()
            return # Don't show success message

        # Finish with options
        await message.answer(
            "✅ Konspekt tayyor!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 AI menyusiga qaytish", callback_data="ai_assistant_main")]
            ])
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos keyinroq urinib ko'ring.")
        await state.clear()


# ============================================================
# 3. GRANT TAQSIMOTI (AI CALCULATION)
# ============================================================
@router.callback_query(F.data == "ai_grant_calc")
async def cb_grant_calc(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        # 1. Premium/Access Check
        allowed, text, _ = await check_premium_access(call.from_user.id, session, "Grant Hisoblash")
        if not allowed:
            return await call.answer(text, show_alert=True)
            
        student = await get_student_by_tg(call.from_user.id, session)
        if not student:
            return await call.answer("Talaba aniqlanmadi", show_alert=True)
            
        # Send "Thinking..." status
        processing_msg = await call.message.edit_text(
            "⏳ <b>Ma'lumotlaringiz tahlil qilinmoqda...</b>\n\n"
            "• GPA ko'rsatkichlaringiz olinmoqda\n"
            "• Tasdiqlangan faolliklaringiz hisoblanmoqda\n"
            "• AI prognoz tayyorlamoqda...",
            parse_mode="HTML"
        )
        
        # 1.5 NAME REFRESH (Force True Name from HEMIS)
        # Grant calculation deals with sensitive personalization, so we ensure name is correct.
        if student.hemis_token:
            try:
                me_data = await HemisService.get_me(student.hemis_token)
                if me_data:
                    f_name_parts = [
                        me_data.get('firstname', ''), 
                        me_data.get('lastname', ''), 
                        me_data.get('fathername', '')
                    ]
                    # Filter empty strings and join
                    f_name = " ".join(filter(None, f_name_parts)).strip()
                    # Fallback if structure is different
                    if not f_name:
                         f_name = f"{me_data.get('firstname','')}".strip()
                         
                    if f_name and len(f_name) > 3:
                        student.full_name = f_name
                        await session.commit()
            except Exception as e:
                logger.error(f"Name refresh failed: {e}")
        
        # 2. Calculate Stats
        hemis_service = HemisService()
        stats = await calculate_grant_score(student, session, hemis_service)
        
        # 3. Construct Prompt for AI
        # Detailed Context
        prompt = (
            f"Talaba ismi: {student.full_name}\n"
            f"GPA: {stats['gpa']} (Maksimum 5.0)\n"
            f"Akademik Ball (GPA x 16): {stats['academic_score']} / 80\n"
            f"Ijtimoiy Faollik Ball (Raw/5): {stats['social_score']} / 20\n"
            f"YAKUNIY BALL: {stats['total_score']} / 100\n\n"
            "FAOLLIKLAR TABLE BO'YICHA HOLAT:\n"
        )
        
        cat_names = {
            "togarak": "To'garaklar (5 tashabbus)",
            "yutuqlar": "Yutuqlar (Olimpiada/Sport)",
            "marifat": "Ma'rifat darslari",
            "volontyorlik": "Volontyorlik",
            "madaniy": "Madaniy tashriflar",
            "sport": "Sport",
            "boshqa": "Boshqa"
        }
        
        for detail in stats['details']:
            cat_key = detail['category']
            name = cat_names.get(cat_key, cat_key.capitalize())
            prompt += f"- {name}: {detail['count']} ta tasdiqlangan (Max ball uchun 7 ta kerak). Berilgan ball: {round(detail['earned'], 1)} (Max {detail['max_points']})\n"
            
        prompt += """
        
        SENING VAZIFANG:
        Yuqoridagi ma'lumotlar asosida talabaga Grant olish imkoniyatini "Grant Taqsimoti va Reglamenti" asosida tushuntirib berish.
        
        ⚠️ QOIDALAR:
        1. Murojaat: "Hurmatli {student.full_name}" deb murojaat qil. (Boshqa ism yoki shablon ishlatma!).
        2. Ohang: Muloyim, lekin kuchli motivatsiya beruvchi. Rasmiyatchilik kamroq bo'lsin, samimiy yordamchi kabi gapir.
        3. Hech qachon "Aniq olasiz" dema. "Taxminiy", "Imkoniyat yuqori/past" deb ayt.
        4. Javob strukturasi:
           - 🎯 Taxminiy ball (Jami xx / 100)
           - 📘 Akademik (GPA) hissasi
           - 🤝 Ijtimoiy faollik hissasi
           - 🔥 Motivatsiya va Harakatga chaqiruv (Qisqa tushuntirish O'RNIGA): Talabaning kuchli tomonini maqtab, kuchsiz tomonini to'g'irlash uchun aniq harakatga unda. "Sizda imkon bor, faqat mana bu narsani qiling" degan ma'noda.
           - 💡 Aniq Reja (Action Plan): Ballni oshirish uchun bajarilishi shart bo'lgan 2-3 ta aniq qadam (masalan: "Ertadan boshlab 'Zakovat' to'garagiga yoziling").
        
        Javobni O'zbek tilida, chiroyli va tushunarli formatda yoz.
        
        FORMATLASH QOIDALARI:
        - Markdown ("**") ishlatma! Faqat HTML teglaridan foydalan:
        - Qalin yozish uchun: <b>matn</b>
        - Kursiv yozish uchun: <i>matn</i>
        - Emojilarni erkin ishlat.
        """
        
        # 4. Generate AI Response
        ai_response = await generate_answer_by_key("grant_calc", prompt)
        
        if not ai_response:
            ai_response = "❌ <b>AI javob bera olmadi.</b>\nIltimos keyinroq urinib ko'ring."
        
        # 5. Send Result
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="ai_assistant_main")]
        ])
        
        await call.message.edit_text(
            ai_response,
            reply_markup=keyboard,
            parse_mode="HTML" # AI Service should return HTML safe text or we sanitize
        )
        
        # 6. Enable Follow-up Chat
        await state.set_state(AIStates.chatting)
        # Save the context so the next user message uses this context instead of generic one
        full_context = f"{prompt}\n\nAI JAVOBI:\n{ai_response}"
        await state.update_data(custom_context=full_context)
        
    except Exception as e:
        logger.error(f"Grant Calc Error: {e}")
        try:
            await call.message.edit_text(
                f"❌ <b>Xatolik yuz berdi:</b>\n{str(e)}\n\nIltimos admin bilan bog'laning.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Ortga", callback_data="ai_assistant_main")]
                ]),
                parse_mode="HTML"
            )
        except:
            pass

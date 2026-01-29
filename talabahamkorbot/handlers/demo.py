from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# ============================================================
# CONFIG / MOCK DATA
# ============================================================

DEMO_CHANNEL_USERNAME = "@PR_klubi"
DEMO_CHANNEL_URL = "https://t.me/PR_klubi"

class DemoStates(StatesGroup):
    menu = State()
    
    # Student Actions
    st_submitting_activity_photo = State()
    st_submitting_activity_text = State()
    st_submitting_appeal_text = State()
    st_submitting_doc_file = State()
    st_submitting_cert_file = State()
    st_submitting_cert_name = State()
    
    # Staff Actions
    staff_replying_appeal = State()
    
    # Tyutor Actions
    tyutor_log_title = State()

# Initial Mock DB Structure
def get_initial_demo_db():
    return {
        "student": {
            "full_name": "Olimov Alisher",
            "faculty": "Axborot texnologiyalari",
            "course": 3,
            "group": "512-21",
            "rating": 85
        },
        "activities": [
            {"id": 1, "type": "Sport", "title": "Futbol musobaqasi", "status": "approved", "date": "15.12.2025"},
        ],
        "documents": [
            {"id": 1, "type": "Obyektivka", "name": "Mening obyektivkam.pdf", "status": "approved", "date": "01.09.2025"},
        ],
        "certificates": [
            {"id": 1, "type": "IELTS", "title": "IELTS 7.0", "status": "pending", "date": "10.12.2025"}
        ],
        "feedbacks": [
             {"id": 1, "to": "Dekanat", "text": "Dars jadvali bo'yicha taklif...", "status": "answered", "reply": "Ko'rib chiqamiz."},
        ],
        "tyutor_logs": [
            {"id": 1, "title": "Ijara xonadoniga tashrif", "description": "Talabalar sharoiti o'rganildi", "status": "pending", "date": "16.12.2025"}
        ]
    }

# ============================================================
# 1. ENTRY POINT
# ============================================================
@router.message(Command("demo"))
async def cmd_demo(message: Message, state: FSMContext):
    # 1. Check Subscription
    try:
        member = await message.bot.get_chat_member(DEMO_CHANNEL_USERNAME, message.from_user.id)
        if member.status in ("left", "kicked"):
            await message.answer(
                "🚀 <b>Demo versiyani ishga tushirish uchun quyidagi kanalga obuna bo'lishingiz shart:</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=DEMO_CHANNEL_URL)],
                    [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_demo_sub")]
                ])
            )
            return
    except Exception:
        pass 

    await start_demo(message, state)


@router.callback_query(F.data == "check_demo_sub")
async def cb_check_demo_sub(call: CallbackQuery, state: FSMContext):
    try:
        member = await call.bot.get_chat_member(DEMO_CHANNEL_USERNAME, call.from_user.id)
        if member.status in ("left", "kicked"):
            await call.answer("❌ Hali a'zo emassiz!", show_alert=True)
            return
    except Exception:
        pass 

    await call.message.delete()
    await start_demo(call.message, state)


async def start_demo(message: Message, state: FSMContext):
    # Initialize Mock DB if not present
    data = await state.get_data()
    if "demo_db" not in data:
        await state.update_data(demo_db=get_initial_demo_db())
    else:
        # DB exists, ensure we clear any pending state from interactions
        await state.set_state(None)
    
    await message.answer(
        "🎭 <b>TalabaHamkor Bot — DEMO (To'liq Versiya)</b>\n\n"
        "Barcha tugmalar qat'iy mantiq bilan ishlaydi.\n"
        "Siz kiritgan ma'lumotlar sessiyada saqlanadi.\n\n"
        "Kim sifatida kirmoqchisiz?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Talaba", callback_data="demo_role:student")],
            [InlineKeyboardButton(text="👨‍💼 Xodim (Rahbariyat/Dekanat/Tyutor)", callback_data="demo_role:staff")],
            [InlineKeyboardButton(text="❌ Demon tugatish", callback_data="demo_exit")]
        ])
    )

# ============================================================
# 2. STUDENT FLOW
# ============================================================
@router.callback_query(F.data == "demo_role:student")
async def demo_student_menu(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    db = data["demo_db"]
    st = db["student"]
    
    # Fake rating calc
    rating = st["rating"] + (len([a for a in db["activities"] if a["status"]=="approved"]) * 5)

    await call.message.edit_text(
        f"🎓 <b>Talaba Kabineti (Demo)</b>\n\n"
        f"👤 <b>{st['full_name']}</b>\n"
        f"🏫 <b>Fakultet:</b> {st['faculty']}\n"
        f"👥 <b>Guruh:</b> {st['group']}\n"
        f"📈 <b>Reyting:</b> {rating} ball\n\n"
        "Barcha bo'limlar ishlaydi. Marhamat:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Profil", callback_data="demo_st:profile")],
            [InlineKeyboardButton(text="📊 Faolliklarim", callback_data="demo_st:activities")],
            [InlineKeyboardButton(text="📄 Hujjatlar", callback_data="demo_st:documents")],
            [InlineKeyboardButton(text="🎓 Sertifikatlar", callback_data="demo_st:certificates")],
            [InlineKeyboardButton(text="📨 Murojaatlar", callback_data="demo_st:feedback_menu")],
            [InlineKeyboardButton(text="⬅️ Rol tanlashga qaytish", callback_data="demo_back_start")]
        ])
    )

@router.callback_query(F.data == "demo_st:profile")
async def demo_st_profile(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "👤 <b>Mening Profilim</b>\n\n"
        "Ism: Olimov Alisher\n"
        "ID: 123456\n"
        "Tel: +998901234567\n"
        "Guruh: 512-21\n"
        "Tyutor: Eshmatov Toshmat",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧑‍🏫 Tyutor haqida", callback_data="demo_st:tutor")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:student")]
        ])
    )

# --- 2.1 Activities ---
@router.callback_query(F.data == "demo_st:activities")
async def demo_st_activities(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    activities = data["demo_db"]["activities"]
    
    text = "📊 <b>Faolliklarim:</b>\n\n"
    if not activities:
        text += "Hozircha bo'sh."
    else:
        for idx, act in enumerate(activities, 1):
            status_icon = "✅" if act['status'] == 'approved' else "⏳"
            text += f"{idx}. {act['title']} ({status_icon})\n"

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Faollik qo'shish", callback_data="demo_st:add_act_menu")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "demo_st:add_act_menu")
async def demo_st_add_act_menu(call: CallbackQuery):
    await call.message.edit_text(
        "➕ <b>Faollik turini tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Sport", callback_data="demo_act_type:Sport")],
            [InlineKeyboardButton(text="Zakovat", callback_data="demo_act_type:Zakovat")],
            [InlineKeyboardButton(text="Tadbir", callback_data="demo_act_type:Tadbir")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_st:activities")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("demo_act_type:"))
async def demo_st_add_act_start(call: CallbackQuery, state: FSMContext):
    atype = call.data.split(":")[1]
    await state.update_data(temp_act_type=atype)
    await state.set_state(DemoStates.st_submitting_activity_photo)
    await call.message.edit_text(
        f"📸 <b>{atype} bo'yicha rasm yuboring:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data="demo_st:activities")]]),
        parse_mode="HTML"
    )

@router.message(DemoStates.st_submitting_activity_photo, F.photo)
async def demo_st_save_photo(message: Message, state: FSMContext):
    await state.update_data(temp_photo=message.photo[-1].file_id)
    await state.set_state(DemoStates.st_submitting_activity_text)
    await message.answer("✍️ <b>Endi esa izoh (nomi)ni yozing:</b>")

@router.message(DemoStates.st_submitting_activity_text)
async def demo_st_save_act(message: Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    db = data["demo_db"]
    atype = data.get("temp_act_type", "General")
    
    new_act = {
        "id": len(db["activities"]) + 1,
        "type": atype,
        "title": text,
        "status": "pending", 
        "date": datetime.now().strftime("%d.%m.%Y"),
        "photo": data.get("temp_photo")
    }
    
    db["activities"].append(new_act)
    await state.update_data(demo_db=db)
    
    await message.answer(
        "✅ <b>Faollik muvaffaqiyatli qo'shildi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Menyuga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

# --- 2.2 Documents ---
@router.callback_query(F.data == "demo_st:documents")
async def demo_st_docs(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    docs = data["demo_db"]["documents"]
    
    text = "📄 <b>Mening Hujjatlarim:</b>\n\n"
    if not docs:
        text += "Hozircha bo'sh."
    else:
        for idx, d in enumerate(docs, 1):
            text += f"{idx}. {d['type']} ({d['date']})\n"

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Hujjat qo'shish", callback_data="demo_st:add_doc_menu")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "demo_st:add_doc_menu")
async def demo_st_add_doc_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📄 <b>Hujjat turini tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Passport nusxasi", callback_data="demo_doc_type:Passport")],
            [InlineKeyboardButton(text="Obyektivka", callback_data="demo_doc_type:Obyektivka")],
            [InlineKeyboardButton(text="Rezyume", callback_data="demo_doc_type:Rezyume")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_st:documents")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("demo_doc_type:"))
async def demo_st_add_doc_start(call: CallbackQuery, state: FSMContext):
    dtype = call.data.split(":")[1]
    await state.update_data(temp_doc_type=dtype)
    await state.set_state(DemoStates.st_submitting_doc_file)
    await call.message.edit_text(
        f"📤 <b>{dtype} faylini yuboring (PDF/DOC):</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data="demo_st:documents")]]),
        parse_mode="HTML"
    )

@router.message(DemoStates.st_submitting_doc_file, F.document)
async def demo_st_save_doc(message: Message, state: FSMContext):
    data = await state.get_data()
    db = data["demo_db"]
    dtype = data.get("temp_doc_type")
    
    new_doc = {
        "id": len(db["documents"]) + 1,
        "type": dtype,
        "name": message.document.file_name,
        "status": "approved", # Auto approve for demo simplicity or pending? Let's say approved for docs usually
        "date": datetime.now().strftime("%d.%m.%Y")
    }
    db["documents"].append(new_doc)
    await state.update_data(demo_db=db)
    
    await message.answer(
        "✅ <b>Hujjat saqlandi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Menyuga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

# --- 2.3 Certificates ---
@router.callback_query(F.data == "demo_st:certificates")
async def demo_st_certs(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    certs = data["demo_db"]["certificates"]
    
    text = "🎓 <b>Sertifikatlarim:</b>\n\n"
    for idx, c in enumerate(certs, 1):
        status = "✅" if c['status'] == 'approved' else "⏳"
        text += f"{idx}. {c['title']} ({status})\n"

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Sertifikat qo'shish", callback_data="demo_st:add_cert")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "demo_st:add_cert")
async def demo_st_add_cert(call: CallbackQuery, state: FSMContext):
    await state.set_state(DemoStates.st_submitting_cert_file)
    await call.message.edit_text(
        "📸 <b>Sertifikat rasmini/faylini yuboring:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data="demo_st:certificates")]]),
        parse_mode="HTML"
    )

@router.message(DemoStates.st_submitting_cert_file, F.photo | F.document)
async def demo_st_cert_file(message: Message, state: FSMContext):
    await state.set_state(DemoStates.st_submitting_cert_name)
    await message.answer("✍️ <b>Sertifikat nomi (masalan IELTS 7.0):</b>")

@router.message(DemoStates.st_submitting_cert_name)
async def demo_st_cert_save(message: Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    db = data["demo_db"]
    
    new_cert = {
        "id": len(db["certificates"]) + 1,
        "type": "Other",
        "title": text,
        "status": "pending",
        "date": datetime.now().strftime("%d.%m.%Y")
    }
    db["certificates"].append(new_cert)
    await state.update_data(demo_db=db)
    
    await message.answer(
        "✅ <b>Sertifikat tekshirishga yuborildi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Menyuga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

# --- 2.4 Feedback ---
@router.callback_query(F.data == "demo_st:feedback_menu")
async def demo_st_feedback_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📩 <b>Murojaat Yuborish</b>\n\n"
        "Kimga murojaat qilmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Rahbariyat", callback_data="demo_fb_to:Rahbariyat")],
            [InlineKeyboardButton(text="🏫 Dekanat", callback_data="demo_fb_to:Dekanat")],
            [InlineKeyboardButton(text="🧠 Psixolog", callback_data="demo_fb_to:Psixolog")],
             [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("demo_fb_to:"))
async def demo_st_fb_start(call: CallbackQuery, state: FSMContext):
    to_who = call.data.split(":")[1]
    await state.update_data(temp_fb_to=to_who)
    await state.set_state(DemoStates.st_submitting_appeal_text)
    
    await call.message.edit_text(
        f"✍️ <b>{to_who} uchun murojaatingizni yozing:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Bekor qilish", callback_data="demo_st:feedback_menu")]]),
        parse_mode="HTML"
    )

@router.message(DemoStates.st_submitting_appeal_text)
async def demo_st_fb_save(message: Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    db = data["demo_db"]
    to_who = data.get("temp_fb_to", "Rahbariyat")
    
    new_fb = {
        "id": len(db["feedbacks"]) + 1,
        "to": to_who,
        "text": text,
        "status": "pending",
        "reply": None,
        "date": datetime.now().strftime("%d.%m.%Y")
    }
    db["feedbacks"].append(new_fb)
    await state.update_data(demo_db=db)
    
    await message.answer(
        "✅ <b>Murojaat yuborildi!</b> Javobni 'Murojaatlar' bo'limida ko'rasiz.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Menyuga", callback_data="demo_role:student")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "demo_st:tutor")
async def demo_st_tutor(call: CallbackQuery):
     await call.message.edit_text(
        "🧑‍🏫 <b>Mening Tyutorim</b>\n\n"
        "👤 <b>F.I.SH:</b> Eshmatov Toshmat\n"
        "📞 <b>Tel:</b> +998901234567\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:student")] ]),
        parse_mode="HTML"
    )

# ============================================================
# 3. STAFF FLOW
# ============================================================
@router.callback_query(F.data == "demo_role:staff")
async def demo_staff_roles_menu(call: CallbackQuery):
    await call.message.edit_text(
        "👨‍💼 <b>Xodim Rolini Tanlang</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Rahbariyat", callback_data="demo_stwf:Rahbariyat")],
            [InlineKeyboardButton(text="🏫 Dekanat", callback_data="demo_stwf:Dekanat")],
            [InlineKeyboardButton(text="🧑‍🏫 Tyutor", callback_data="demo_stwf:Tyutor")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_back_start")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("demo_stwf:"))
async def demo_staff_dashboard(call: CallbackQuery, state: FSMContext):
    role = call.data.split(":")[1]
    data = await state.get_data()
    db = data["demo_db"]
    
    # Tyutor Logic
    if role == "Tyutor":
        logs = db["tyutor_logs"]
        await call.message.edit_text(
            f"🖥 <b>Tyutor Dashboardi</b>\n\n"
            f"👥 <b>Guruh:</b> 512-21 (25 talaba)\n"
            f"✅ <b>KPI:</b> 45 ball\n"
            f"📝 <b>Hisobotlar:</b> {len(logs)} ta",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 6 yo'nalish hisobot", callback_data="demo_tyutor:logs")],
                [InlineKeyboardButton(text="🔍 Talaba qidirish", callback_data="demo_tyutor:search")],
                [InlineKeyboardButton(text="⬅️ Rol almashtirish", callback_data="demo_role:staff")]
            ]),
            parse_mode="HTML"
        )
        return

    # Rahbariyat / Dekanat Logic
    # Filter pending items
    pending_acts = [a for a in db["activities"] if a["status"] == "pending"]
    pending_logs = [l for l in db["tyutor_logs"] if l["status"] == "pending"]
    pending_feeds = [f for f in db["feedbacks"] if f["status"] == "pending" and f["to"] == role]
    
    await call.message.edit_text(
        f"🖥 <b>{role} Dashboardi (Demo)</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"• Talabalar: {1200 + len(db['activities'])}\n" 
        f"• Faollik arizalari: <b>{len(pending_acts)}</b>\n"
        f"• Murojaatlar ({role}ga): <b>{len(pending_feeds)}</b>\n",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Faolliklar ({len(pending_acts)})", callback_data="demo_list:acts")],
            [InlineKeyboardButton(text=f"📩 Murojaatlar ({len(pending_feeds)})", callback_data="demo_list:feeds")],
             # Only Rahbariyat sees Tyutor logs usually, but let's allow both for demo
            [InlineKeyboardButton(text=f"📋 Tyutor Hisobot ({len(pending_logs)})", callback_data="demo_list:logs")],
            [InlineKeyboardButton(text="📊 Hisobot yuklab olish", callback_data="demo_dl_report")],
            [InlineKeyboardButton(text="⬅️ Rol almashtirish", callback_data="demo_role:staff")]
        ])
    )

# --- 3.1 Staff Activtiy Approval ---
@router.callback_query(F.data == "demo_list:acts")
async def demo_list_acts(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    db = data["demo_db"]
    pending = [a for a in db["activities"] if a["status"] == "pending"]
    
    if not pending:
         await call.answer("📭 Yangi arizalar yo'q", show_alert=True)
         return

    act = pending[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"demo_do_act:ok:{act['id']}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"demo_do_act:no:{act['id']}")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:staff")]
    ])
    
    caption = f"🏆 <b>{act['type']}</b>\n📝 {act['title']}\n📅 {act['date']}"
    
    if act.get("photo"):
        await call.message.delete()
        await call.message.answer_photo(act["photo"], caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await call.message.edit_text(caption, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("demo_do_act:"))
async def demo_do_act(call: CallbackQuery, state: FSMContext):
    action, aid = call.data.split(":")[1:]
    aid = int(aid)
    data = await state.get_data()
    db = data["demo_db"]
    
    for a in db["activities"]:
        if a["id"] == aid:
            a["status"] = "approved" if action == "ok" else "rejected"
            break
            
    await state.update_data(demo_db=db)
    await call.answer("✅ Bajarildi!")
    
    # Refresh logic simplified: Check if more pending
    pending = [a for a in db["activities"] if a["status"] == "pending"]
    if pending:
        await demo_list_acts(call, state)
    else:
        # If message was photo, delete it and send text
        if call.message.photo:
            await call.message.delete()
            await call.message.answer("🎉 Barcha arizalar tugadi!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Dashboard", callback_data="demo_role:staff")]]))
        else:
             await call.message.edit_text("🎉 Barcha arizalar tugadi!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Dashboard", callback_data="demo_role:staff")]]))

# --- 3.2 Staff Appeal Reply ---
@router.callback_query(F.data == "demo_list:feeds")
async def demo_list_feeds(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    db = data["demo_db"]
    # Get current role from text context or store logic? 
    # Current limitation: we don't know easily which role menu we came from without storing it.
    # We will show ALL pending for demo simplicity or try to infer.
    # Let's show all pending.
    pending = [f for f in db["feedbacks"] if f["status"] == "pending"]
    
    if not pending:
         await call.answer("📭 Yangi murojaat yo'q", show_alert=True)
         return

    fb = pending[0]
    await call.message.edit_text(
        f"📩 <b>Murojaat (#{fb['id']})</b>\n"
        f"KIMGA: {fb['to']}\n\n"
        f"📝 <b>Matn:</b> {fb['text']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Javob yozish", callback_data=f"demo_rep:{fb['id']}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:staff")]
        ])
    )

@router.callback_query(F.data.startswith("demo_rep:"))
async def demo_rep_start(call: CallbackQuery, state: FSMContext):
    fid = int(call.data.split(":")[1])
    await state.update_data(reply_fid=fid)
    await state.set_state(DemoStates.staff_replying_appeal)
    await call.message.edit_text("✍️ <b>Javob matnini kiriting:</b>")

@router.message(DemoStates.staff_replying_appeal)
async def demo_rep_save(message: Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    db = data["demo_db"]
    fid = data.get("reply_fid")
    
    for f in db["feedbacks"]:
        if f["id"] == fid:
            f["status"] = "answered"
            f["reply"] = text
            break
            
    await state.update_data(demo_db=db)
    await message.answer("✅ Javob yuborildi!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Dashboard", callback_data="demo_role:staff")]]))

# --- 3.3 Tyutor Logs & Flows ---
@router.callback_query(F.data == "demo_tyutor:logs")
async def demo_tyutor_logs(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    logs = data["demo_db"]["tyutor_logs"]
    
    text = "📝 <b>6 yo'nalish hisobotlari:</b>\n"
    for l in logs:
        text += f"- {l['title']} ({l['status']})\n"
        
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi hisobot", callback_data="demo_tyutor:add_log")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_stwf:Tyutor")]
    ]))

@router.callback_query(F.data == "demo_tyutor:add_log")
async def demo_tyutor_add_log(call: CallbackQuery, state: FSMContext):
    # Simpler add flow
    data = await state.get_data()
    db = data["demo_db"]
    new_log = {
        "id": len(db["tyutor_logs"]) + 1, "title": "Yangi hisobot (Demo)", "description": "...", "status": "pending", "date": "Now"
    }
    db["tyutor_logs"].append(new_log)
    await state.update_data(demo_db=db)
    await call.answer("✅ Qo'shildi!", show_alert=True)
    await demo_tyutor_logs(call, state)

@router.callback_query(F.data == "demo_tyutor:search")
async def demo_tyutor_search(call: CallbackQuery):
    await call.message.edit_text("🔍 <b>Talaba qidirish:</b>\n\nIsm kiriting:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔎 Qidirish (Alisher)", callback_data="demo_tyutor:do_search")]]))

@router.callback_query(F.data == "demo_tyutor:do_search")
async def demo_tyutor_do_search(call: CallbackQuery):
    await call.message.edit_text("✅ Topildi: Olimov Alisher", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_stwf:Tyutor")]]))

@router.callback_query(F.data == "demo_list:logs")
async def demo_approve_logs(call: CallbackQuery, state: FSMContext):
    # Simplified approval
    data = await state.get_data()
    db = data["demo_db"]
    pending = [l for l in db["tyutor_logs"] if l["status"] == "pending"]
    if not pending:
         await call.answer("Bo'sh!", show_alert=True); return
         
    l = pending[0]
    await call.message.edit_text(f"📋 {l['title']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tasdiqlash", callback_data=f"demo_do_log:{l['id']}")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="demo_role:staff")]
    ]))
    
@router.callback_query(F.data.startswith("demo_do_log:"))
async def demo_do_log(call: CallbackQuery, state: FSMContext):
    lid = int(call.data.split(":")[1])
    data = await state.get_data()
    db = data["demo_db"]
    for l in db["tyutor_logs"]:
        if l["id"] == lid: l["status"] = "approved"
    await state.update_data(demo_db=db)
    await call.answer("✅")
    await call.message.edit_text("Tasdiqlandi.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Ortga", callback_data="demo_role:staff")]]))


# --- 3.4 Reports Download ---
@router.callback_query(F.data == "demo_dl_report")
async def demo_dl_report(call: CallbackQuery):
    # Mock file
    await call.answer("📊 Hisobot tayyorlanmoqda...", show_alert=False)
    # Send a dummy text file as report
    dummy_file = BufferedInputFile(b"Demo Report Data...", filename="hisobot_demo.xlsx")
    await call.message.answer_document(dummy_file, caption="📊 <b>Siz so'ragan hisobot (Demo)</b>", parse_mode="HTML")

# ============================================================
# 4. UTILS
# ============================================================
@router.callback_query(F.data == "demo_back_start")
async def demo_back_start(call: CallbackQuery, state: FSMContext):
    await start_demo(call.message, state)

@router.callback_query(F.data == "demo_exit")
async def demo_exit(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Demo rejim tugatildi. /start ni bosing.")
    await state.clear()

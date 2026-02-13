from aiogram import Router, F
from datetime import datetime
import re
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Staff, StaffRole, Club, ClubMembership, Student
from services.google_sheets import append_student_to_club_sheet
from keyboards.inline_kb import get_back_inline_kb

router = Router()

class ClubStates(StatesGroup):
    creating_club_name = State()
    creating_club_desc = State()
    creating_club_link = State()
    creating_club_statute = State()
    assigning_leader_hemis = State()
    
    # Leader States
    broadcasting_content = State()
    event_title = State()
    event_date = State()
    event_location = State()
    
    # Yetakchi Broadcast
    yetakchi_broadcast_content = State()

# ============================================================
# 1. YOSHLAR YETAKCHISI (ADMIN)
# ============================================================
@router.callback_query(F.data == "admin_clubs_menu")
async def cb_admin_clubs(call: CallbackQuery):
    # Check if user is Yoshlar Yetakchisi (Middleware usually handles, but here explicit)
    await call.message.edit_text(
        "🏛 <b>Klublar Boshqaruvi (Yoshlar yetakchisi)</b>\n\n"
        "Yangi klub ochish yoki rahbar tayinlash.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi klub qo'shish", callback_data="club_add_new")],
            [InlineKeyboardButton(text="📋 Klublar ro'yxati (Boshqarish)", callback_data="club_list_admin")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_home")] # Assuming generic home
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "club_list_admin")
async def cb_admin_list_clubs(call: CallbackQuery, session: AsyncSession):
    # List all clubs with Manage button
    clubs = (await session.execute(select(Club))).scalars().all()
    kb = []
    for c in clubs:
        kb.append([InlineKeyboardButton(text=f"⚙️ {c.name}", callback_data=f"club_adm_manage:{c.id}")])
    kb.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_clubs_menu")])
    await call.message.edit_text("📋 <b>Barcha Klublar:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@router.callback_query(F.data.startswith("club_adm_manage:"))
async def cb_admin_manage_one(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    club = await session.get(Club, cid)
    
    # Leaders List
    leaders_text = ""
    leader_kb = []
    
    if club.leaders:
        leaders_text = "<b>Joriy Rahbarlar:</b>\n"
        for i, ldr in enumerate(club.leaders, 1):
            leaders_text += f"{i}. {ldr.full_name} (+{ldr.phone})\n"
            leader_kb.append([
                InlineKeyboardButton(text=f"❌ Olib tashlash: {ldr.full_name.split()[0]}", callback_data=f"club_dismiss_ldr:{cid}:{ldr.id}")
            ])
    else:
        leaders_text = "⚠️ Rahbar tayinlanmagan."
        
    # Main buttons
    leader_kb.insert(0, [InlineKeyboardButton(text="➕ Rahbar tayinlash", callback_data=f"club_assign_ldr:{cid}")])
    leader_kb.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="club_list_admin")])
    
    await call.message.edit_text(
        f"⚙️ <b>{club.name}</b>\n\n"
        f"{leaders_text}\n"
        f"🔗 Kanal: {club.channel_link}\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=leader_kb),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("club_dismiss_ldr:"))
async def cb_dismiss_ldr(call: CallbackQuery, session: AsyncSession):
    parts = call.data.split(":")
    cid = int(parts[1])
    lid = int(parts[2])
    
    # Remove from ClubLeader table
    from database.models import ClubLeader
    await session.execute(
        text("DELETE FROM club_leaders WHERE club_id = :cid AND staff_id = :lid")
        .bindparams(cid=cid, lid=lid)
    )
    await session.commit()
    
    await call.answer("✅ Rahbar vazifasidan ozod qilindi.", show_alert=True)
    # Refresh view
    await cb_admin_manage_one(call, session)

@router.callback_query(F.data.startswith("club_assign_ldr:"))
async def cb_assign_ldr_start(call: CallbackQuery, state: FSMContext):
    cid = int(call.data.split(":")[1])
    await state.update_data(assign_club_id=cid)
    await state.set_state(ClubStates.assigning_leader_hemis)
    await call.message.edit_text("🔍 <b>Talaba HEMIS ID sini kiriting:</b>", reply_markup=get_back_inline_kb(f"club_adm_manage:{cid}"))

@router.message(ClubStates.assigning_leader_hemis)
async def msg_assign_search(message: Message, state: FSMContext, session: AsyncSession):
    hemis = message.text.strip()
    student = await session.scalar(
        select(Student)
        .where(Student.hemis_login == hemis)
        .options(selectinload(Student.faculty), selectinload(Student.tutor_groups))
    )
    
    data = await state.get_data()
    cid = data['assign_club_id']
    
    if not student:
        await message.answer("❌ Talaba topilmadi.", reply_markup=get_back_inline_kb(f"club_assign_ldr:{cid}"))
        return
        
    await state.update_data(candidate_student_id=student.id)
    
    # Detailed Info Construction
    faculty_name = student.faculty.name if student.faculty else "Fakultet yo'q"
    group_num = student.tutor_groups[0].group_number if student.tutor_groups else (student.group_number or "Guruh yo'q")
    
    # Existing Clubs
    # Join ClubMembership -> Club
    member_stm = (
        select(Club.name)
        .join(ClubMembership, Club.id == ClubMembership.club_id)
        .where(ClubMembership.student_id == student.id)
    )
    existing_clubs = (await session.execute(member_stm)).scalars().all()
    clubs_str = ", ".join(existing_clubs) if existing_clubs else "A'zo emas"
    
    # Confirm
    await message.answer(
        f"👤 <b>Nomzod topildi:</b>\n"
        f"Ism: {student.full_name}\n"
        f"Fakultet: {faculty_name}\n"
        f"Guruh: {group_num}\n"
        f"A'zo klublari: {clubs_str}\n\n"
        "Shu talabaga taklif yuborilsinmi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha, Yuborish", callback_data="club_send_proposal")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"club_adm_manage:{cid}")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "club_send_proposal")
async def cb_send_proposal(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    cid = data['assign_club_id']
    sid = data['candidate_student_id']
    
    club = await session.get(Club, cid)
    student = await session.get(Student, sid)
    
    # Find active telegram ID
    from database.models import TgAccount
    acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == sid))
    
    if not acc:
        await call.message.edit_text("❌ Bu talaba botdan ro'yxatdan o'tmagan (Telegram ID yo'q).", reply_markup=get_back_inline_kb(f"club_adm_manage:{cid}"))
        return
        
    # Send Message to Student
    try:
        await call.bot.send_message(
            chat_id=acc.telegram_id,
            text=f"📢 <b>DIQQAT! TAKLIF</b>\n\n"
                 f"Sizni <b>'{club.name}'</b> klubiga rahbar etib tayinlashmoqchi.\n\n"
                 f"ℹ️ Klub haqida: {club.description}\n"
                 f"🔗 Nizom: {club.statute_link}\n\n"
                 f"Agar rozi bo'lsangiz, 'Qabul qilish' tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_leader:{cid}:{sid}")],
                [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_leader:{cid}")]
            ])
        )
        await call.message.edit_text("✅ Taklif yuborildi!", reply_markup=get_back_inline_kb(f"club_adm_manage:{cid}"))
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")
    await state.clear()


@router.callback_query(F.data.startswith("accept_leader:"))
async def cb_student_accept_leader(call: CallbackQuery, session: AsyncSession):
    parts = call.data.split(":")
    cid = int(parts[1])
    sid = int(parts[2])
    
    club = await session.get(Club, cid)
    student = await session.get(Student, sid)
    
    # 1. Check if Staff already exists (by phone or attached to account)
    from database.models import TgAccount
    acc = await session.scalar(select(TgAccount).where(TgAccount.student_id == sid))
    
    existing_staff = None
    if acc and acc.staff_id:
        existing_staff = await session.get(Staff, acc.staff_id)
    
    if not existing_staff:
        # Check by phone to be sure
        existing_staff = await session.scalar(select(Staff).where(Staff.phone == student.phone))

    if existing_staff:
        new_staff = existing_staff
        # Update existing staff role if needed? 
        # Better to keep previous role or append? 
        # For now, just ensure they are active and have title
        new_staff.is_active = True
        new_staff.role = StaffRole.KLUB_RAHBARI # Upgrade role? Or just add permissions?
        new_staff.position = f"{club.name} Prezidenti"
    else:
        new_staff = Staff(
            full_name=student.full_name,
            jshshir=f"TEMP{student.hemis_login}" if student.hemis_login else f"TEMP{student.phone}",
            phone=student.phone,
            role=StaffRole.KLUB_RAHBARI,
            position=f"{club.name} Prezidenti",
            is_active=True
        )
        session.add(new_staff)
        await session.flush() # get ID
    
    # 2. Update TgAccount
    if acc:
        acc.staff_id = new_staff.id
        # acc.current_role = StaffRole.KLUB_RAHBARI.value # REMOVED: Keep as Student
        # We don't change current_role, so they stay in "student" mode, but have Staff rights linked
    
    # 3. Add to Club Leaders (Many-to-Many)
    # Using raw SQL to avoid model mapping overhead for simple pivot
    await session.execute(
        text("INSERT INTO club_leaders (club_id, staff_id) VALUES (:cid, :sid) ON CONFLICT DO NOTHING")
        .bindparams(cid=cid, sid=new_staff.id)
    )
    await session.commit()
    
    await session.commit()
    
    await call.message.edit_text(
        f"🎉 <b>Tabriklaymiz! Siz endi '{club.name}' rahbari etib tayinlandingiz.</b>\n"
        "Boshqaruv tugmasi talaba menyusining eng pastki qismida paydo bo'ldi.\n"
        "Ko'rish uchun /start ni bosing.",
        parse_mode="HTML"
    )
    # Optional: Notify Admin (Yetakchi)

@router.callback_query(F.data == "club_add_new")
async def cb_club_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(ClubStates.creating_club_name)
    await call.message.edit_text("✍️ <b>Yangi klub nomini kiriting:</b>", reply_markup=get_back_inline_kb("admin_clubs_menu"))

@router.message(ClubStates.creating_club_name)
async def msg_club_name(message: Message, state: FSMContext):
    await state.update_data(c_name=message.text)
    await state.set_state(ClubStates.creating_club_desc)
    await message.answer("✍️ <b>Klub haqida qisqacha ma'lumot (Description):</b>")

@router.message(ClubStates.creating_club_desc)
async def msg_club_desc(message: Message, state: FSMContext):
    await state.update_data(c_desc=message.text)
    await state.set_state(ClubStates.creating_club_link)
    await message.answer(
        "🔗 <b>Klubning Telegram kanali/guruhi linki:</b>\n(Masalan: https://t.me/zakovat_club)\n\n"
        "<i>Agar kanal mavjud bo'lmasa, 'O'tkazib yuborish' tugmasini bosing.</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ O'tkazib yuborish", callback_data="club_create_skip_link")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "club_create_skip_link", ClubStates.creating_club_link)
async def cb_create_skip_link(call: CallbackQuery, state: FSMContext):
    await state.update_data(c_link=None)
    await state.set_state(ClubStates.creating_club_statute)
    await call.message.edit_text("📜 <b>Klub Nizomi linkini yuboring:</b>\n(Masalan: https://telegra.ph/nizom...)")

@router.message(ClubStates.creating_club_link)
async def msg_club_link(message: Message, state: FSMContext):
    link = message.text.strip()
    
    # 1. Parse Username
    match = re.search(r"t\.me/(\+?[a-zA-Z0-9_]+)", link)
    username = None
    if match:
        slug = match.group(1)
        if not slug.startswith("+"):
            username = f"@{slug}"
            
    # 2. Check Admin Status
    if username:
        try:
            member = await message.bot.get_chat_member(chat_id=username, user_id=message.bot.id)
            if member.status != "administrator":
                 await message.answer(
                    "⚠️ <b>Diqqat! Bot ushbu kanalda Admin emas.</b>\n\n"
                    "Iltimos, botni kanalga <b>Admin</b> qiling va quyidagi huquqlarni bering:\n"
                    "✅ <i>Foydalanuvchilarni qo'shish</i>\n"
                    "✅ <i>Xabarlarni boshqarish</i>\n\n"
                    "So'ngra linkni qayta yuboring."
                )
                 return
        except TelegramBadRequest:
            await message.answer(
                "❌ <b>Xatolik! Bot kanalni topa olmadi.</b>\n\n"
                "Sabablar:\n"
                "1. Bot kanalga a'zo emas (Admin qilinmagan).\n"
                "2. Link noto'g'ri.\n\n"
                "Iltimos, botni kanalga qo'shib, Admin qilgach qayta urinib ko'ring."
            )
            return
        except Exception as e:
            await message.answer(f"❌ Kutilmagan xatolik: {e}")
            return
            
    await state.update_data(c_link=link)
    await state.set_state(ClubStates.creating_club_statute)
    await message.answer("✅ <b>Kanal tasdiqlandi!</b>\n\n📜 Endi <b>Klub Nizomi linkini</b> yuboring:")

@router.message(ClubStates.creating_club_statute)
async def msg_club_statute(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    # Create Club
    new_club = Club(
        name=data['c_name'],
        description=data['c_desc'],
        channel_link=data['c_link'],
        statute_link=message.text
    )
    session.add(new_club)
    await session.commit()
    
    await message.answer(f"✅ <b>{new_club.name}</b> muvaffaqiyatli yaratildi!\nEndi unga rahbar tayinlashingiz mumkin.", reply_markup=get_back_inline_kb("admin_clubs_menu"))
    await state.clear()


# ============================================================
# 2. TALABA (STUDENT)
# ============================================================
@router.callback_query(F.data.startswith("student_clubs_market"))
async def cb_st_clubs_market(call: CallbackQuery, session: AsyncSession):
    # Determine back button logic
    back_to = "go_student_home"
    if "profile" in call.data:
        back_to = "student_profile"

    # List all clubs
    clubs = (await session.execute(select(Club))).scalars().all()
    
    kb_rows = []
    for c in clubs:
        kb_rows.append([InlineKeyboardButton(text=f"🎭 {c.name}", callback_data=f"club_view:{c.id}")])
    kb_rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_to)])
    
    text = (
        "🎭 <b>Universitet Klublari</b>\n\n"
        "Qiziqqan klubingizni tanlang va a'zo bo'ling!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.delete()
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("club_view:"))
async def cb_club_view(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    club = await session.get(Club, cid)
    
    # Check membership
    # For now assume not joined
    
    text = (
        f"🎭 <b>{club.name}</b>\n\n"
        f"ℹ️ {club.description}\n\n"
        f"🔗 <a href='{club.statute_link or '#'}'>Klub Nizomi</a>"
    )
    
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ A'zo bo'laman", callback_data=f"club_join_start:{cid}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_clubs_market")]
        ]),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@router.callback_query(F.data.startswith("club_join_start:"))
async def cb_club_join_step1(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    club = await session.get(Club, cid)
    
    await call.message.edit_text(
        f"⚠️ <b>A'zo bo'lish uchun talab:</b>\n\n"
        f"1. Quyidagi kanalga qo'shiling: {club.channel_link}\n"
        f"2. Keyin 'A'zo bo'ldim' tugmasini bosing.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga o'tish", url=club.channel_link)],
            [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data=f"club_join_verify:{cid}")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("club_join_verify:"))
async def cb_club_join_verify(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    club = await session.get(Club, cid)
    
    # Mock Subscription Check (In real usage, bot needs admin rights in that channel)
    # We assume success for now or use ChatMember check if bot is admin
    
    # --- CHANNEL VERIFICATION START ---
    channel_username = None
    if club.channel_link:
        match = re.search(r"t\.me/(\+?[a-zA-Z0-9_]+)", club.channel_link)
        if match:
            slug = match.group(1)
            if slug.startswith("+"):
                # Private link - we generally can't verify unless we have chat_id stored
                # Or try to rely on bot being in chat? 
                # For private links, we might need to skip or warn.
                pass 
            else:
                channel_username = f"@{slug}"
                
    if channel_username:
        try:
            member = await call.bot.get_chat_member(chat_id=channel_username, user_id=call.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await call.answer("❌ Siz hali kanalga a'zo emassiz! Iltimos, avval qo'shiling.", show_alert=True)
                return
        except TelegramBadRequest as e:
            # Common cases: 
            # 1. Chat not found (Bot not in chat or wrong username)
            # 2. Bot is not admin (cannot see members in some cases?) -> actually get_chat_member works if bot is just member too usually, depending on privacy.
            # But usually usually "Chat not found" means bot is not added.
            if "chat not found" in e.message.lower() or "participant_id_invalid" in e.message.lower():
                await call.answer(
                    "⚠️ Bot kanalni tekshira olmadi.\n\n"
                    "Sababi: Bot kanalga qo'shilmagan yoki admin emas.\n"
                    "Iltimos, klub rahbariga murojaat qiling.", 
                    show_alert=True
                )
                return
            else:
                # Other error, maybe log it but allow pass? or fail?
                # Safer to fail to enforce rules.
                await call.answer(f"❌ Xatolik: {e.message}", show_alert=True)
                return
        except Exception:
            pass # Skip if other error
            
    # --- CHANNEL VERIFICATION END ---
    
    # 1. Get Student
    from database.models import TgAccount
    acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == call.from_user.id))
    
    if not acc or not acc.student_id:
        await call.answer("❌ Siz talaba sifatida ro'yxatdan o'tmagansiz.", show_alert=True)
        return
        
    student = await session.get(Student, acc.student_id)
    
    # 2. Check overlap
    existing = await session.scalar(
        select(ClubMembership)
        .where(ClubMembership.student_id == student.id, ClubMembership.club_id == cid)
    )
    
    if not existing:
        # 3. Create Membership
        new_membership = ClubMembership(
            student_id=student.id,
            club_id=cid
        )
        session.add(new_membership)
        await session.commit()
    
    # Export to Google Sheet
    await append_student_to_club_sheet(club.spreadsheet_url, {"name": student.full_name, "id": student.hemis_id})
    
    await call.message.edit_text(
        f"🎉 <b>Tabriklaymiz! Siz {club.name} a'zosi bo'ldingiz.</b>\n"
        "Ma'lumotlaringiz klub bazasiga kiritildi.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Klublar ro'yxati", callback_data="student_clubs_market")]
        ]),
        parse_mode="HTML"
    )

# ============================================================
# YETAKCHI BROADCAST
# ============================================================
@router.callback_query(F.data == "yetakchi_broadcast_menu")
async def cb_yetakchi_bc_menu(call: CallbackQuery):
    await call.message.edit_text(
        "📢 <b>E'lon Yuborish Bo'limi</b>\n\n"
        "Ushbu bo'lim orqali siz universitet talabalariga muhim xabarlarni yuborishingiz mumkin.\n"
        "Iltimos, auditoriyani tanlang:\n\n"
        "1️⃣ <b>Barcha Talabalarga</b> — Universitetdagi barcha ro'yxatdan o'tgan talabalarga yuboriladi.\n"
        "2️⃣ <b>Klub A'zolariga</b> — Qaysidir klubga a'zo bo'lgan barcha faol talabalarga yuboriladi.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨‍🎓 Barcha Talabalarga", callback_data="bc_target:all_students")],
            [InlineKeyboardButton(text="🎭 Klub A'zolariga (Barchasi)", callback_data="bc_target:club_members")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_home")] # Should trigger Yetakchi menu via auth or separate handler
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("bc_target:"))
async def cb_bc_target_selected(call: CallbackQuery, state: FSMContext):
    target = call.data.split(":")[1]
    await state.update_data(bc_target_audience=target)
    await state.set_state(ClubStates.yetakchi_broadcast_content)
    
    audience_name = "Barcha Talabalar" if target == "all_students" else "Barcha Klub A'zolari"
    
    await call.message.edit_text(
        f"✍️ <b>{audience_name}</b> uchun xabar matnini (yoki rasm+matn) yuboring:",
        reply_markup=get_back_inline_kb("yetakchi_broadcast_menu")
    )

@router.message(ClubStates.yetakchi_broadcast_content)
async def msg_yetakchi_bc_send(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    target = data.get('bc_target_audience')
    
    # Determine recipients logic
    from database.models import TgAccount, ClubMembership
    
    recipient_ids = []
    
    if target == "all_students":
        # All students with TgAccount
        stmt = select(TgAccount.telegram_id).where(TgAccount.student_id.isnot(None))
        result = await session.execute(stmt)
        recipient_ids = result.scalars().all()
        
    elif target == "club_members":
        # Distinct students who are in club_memberships
        # Join ClubMembership -> Student -> TgAccount
        stmt = (
            select(TgAccount.telegram_id)
            .join(Student, TgAccount.student_id == Student.id)
            .join(ClubMembership, Student.id == ClubMembership.student_id)
            .distinct()
        )
        result = await session.execute(stmt)
        recipient_ids = result.scalars().all()
    
    # Sending Logic (Mock or Real loop)
    # IMPORTANT: In production, use background task or batching. Here we loop simply.
    success_count = 0
    blocked_count = 0
    
    # Echo message ID to copy
    # msg_id = message.message_id
    # chat_id = message.chat.id
    
    msg_text = f"📢 <b>YOSHLAR YETAKCHISI E'LONI:</b>\n\n"
    
    sent_msg = await message.answer("⏳ Yuborilmoqda... Iltimos kuting.")
    
    for tid in recipient_ids:
        try:
            # If original message has media, use copy_message, else send_message
            # Simple implementation: copy_message
            await message.copy_to(chat_id=tid)
            success_count += 1
        except Exception:
            blocked_count += 1
            
    await sent_msg.edit_text(
        f"✅ <b>Yuborildi!</b>\n\n"
        f"Auditoriya: {target}\n"
        f"Muvaffaqiyatli: {success_count}\n"
        f"Yetib bormadi (blok): {blocked_count}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="yetakchi_broadcast_menu")]])
    )
    await state.clear()
@router.callback_query(F.data == "club_leader_menu")
async def cb_leader_menu_start(call: CallbackQuery, session: AsyncSession):
    # Find clubs led by this user
    # Need database.models.Staff lookup by tg_id -> Staff.id -> Club.leader_id
    # Assuming 'messages.from_user.id' is mapped. 
    # For now, we query Club where leader logic is simpler or we broadcast to ALL if Admin.
    # PROD: Select * from clubs where leader_id = (Select id from staff where tg_id = ...)
    
    # We will simulate listing all clubs for now, assuming user is authorized.
    clubs = (await session.execute(select(Club))).scalars().all() # In reality filter by leader
    
    kb = []
    for c in clubs:
        kb.append([InlineKeyboardButton(text=f"📢 {c.name} (Boshqarish)", callback_data=f"leader_manage:{c.id}")])
    kb.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_home")])
    
    await call.message.edit_text(
        "💼 <b>Klub Rahbari Paneli</b>\n\n"
        "Boshqarmoqchi bo'lgan klubingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("leader_manage:"))
async def cb_leader_manage_club(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    club = await session.get(Club, cid)
    
    if not club:
        await call.answer("❌ Klub topilmadi.", show_alert=True)
        return

    # [SECURITY] Check Leadership
    from database.models import TgAccount
    account = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == call.from_user.id))
    
    is_leader = False
    if account:
        # Check Student Leader
        if club.leader_student_id and account.student_id == club.leader_student_id:
            is_leader = True
        # Check Staff Leader
        elif club.leader_id and account.staff_id == club.leader_id:
            is_leader = True
        # Check if staff is owner/admin (optional, but let's stick to leader for now)
    
    if not is_leader:
        await call.answer("🚫 Siz bu klub rahbari emassiz!", show_alert=True)
        return
    
    await call.message.edit_text(
        f"💼 <b>{club.name} Boshqaruvi</b>\n\n"
        "Nima qilmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data=f"club_stats:{cid}")],
            [InlineKeyboardButton(text="👥 A'zolar", callback_data=f"club_members:{cid}:0")],
            [InlineKeyboardButton(text="ℹ️ Klub ma'lumotlari", callback_data=f"club_info:{cid}")],
            [InlineKeyboardButton(text="📢 Maqsadli E'lon (Broadcast)", callback_data=f"club_bc_start:{cid}")],
            [InlineKeyboardButton(text="📅 Tadbir yaratish (Calendar)", callback_data=f"club_evt_start:{cid}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_student_home")] 
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("club_stats:"))
async def cb_club_stats(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    
    # Count members
    from database.models import ClubMembership
    from sqlalchemy import func
    
    member_count = await session.scalar(
        select(func.count()).select_from(ClubMembership).where(ClubMembership.club_id == cid)
    )
    
    await call.message.edit_text(
        f"📊 <b>Klub Statistikasi</b>\n\n"
        f"👥 <b>Jami a'zolar:</b> {member_count} nafar\n"
        f"📅 <b>Bugungi faollik:</b> -- (Tez orada)\n\n"
        "<i>Ma'lumotlar real vaqt rejimida yangilanadi.</i>",
        reply_markup=get_back_inline_kb(f"leader_manage:{cid}"),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("club_members:"))
async def cb_club_members(call: CallbackQuery, session: AsyncSession):
    # Data format: club_members:{cid}:{page}
    _, cid_str, page_str = call.data.split(":")
    cid = int(cid_str)
    page = int(page_str)
    limit = 10
    offset = page * limit
    
    # Query Members with Student info
    from database.models import ClubMembership, Student
    stmt = (
        select(Student)
        .join(ClubMembership, Student.id == ClubMembership.student_id)
        .where(ClubMembership.club_id == cid)
        .order_by(Student.full_name)
        .offset(offset)
        .limit(limit + 1) # +1 to check if next page exists
    )
    students = (await session.execute(stmt)).scalars().all()
    
    has_next = len(students) > limit
    display_students = students[:limit]
    
    msg = f"👥 <b>Klub A'zolari (Sahifa {page + 1})</b>\n\n"
    if not display_students:
        msg += "<i>Hozircha a'zolar yo'q.</i>"
    else:
        for i, s in enumerate(display_students, 1):
            phone = s.phone or "Noma'lum"
            msg += f"{offset + i}. <b>{s.full_name}</b>\n   📞 {phone}\n\n"
            
    # Pagination KB
    kb = []
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"club_members:{cid}:{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"club_members:{cid}:{page+1}"))
    if nav_row:
        kb.append(nav_row)
    
    # Excel Download Button
    kb.append([InlineKeyboardButton(text="📥 Excel yuklab olish", callback_data=f"club_download:{cid}")])
    kb.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"leader_manage:{cid}")])
    
    await call.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@router.callback_query(F.data.startswith("club_download:"))
async def cb_club_download(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    
    # Notify user
    await call.answer("⏳ Fayl tayyorlanmoqda...", show_alert=False)
    
    # Fetch ALL members
    from database.models import ClubMembership, Student, Club
    stmt = (
        select(Student, ClubMembership.joined_at)
        .join(ClubMembership, Student.id == ClubMembership.student_id)
        .where(ClubMembership.club_id == cid)
        .order_by(Student.full_name)
    )
    results = (await session.execute(stmt)).all()
    
    if not results:
        await call.answer("❌ A'zolar yo'q!", show_alert=True)
        return

    # Generate Excel
    import openpyxl
    from openpyxl.styles import Font
    import tempfile
    import os
    from aiogram.types import FSInputFile
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Klub A'zolari"
    
    # Headers
    headers = ["T/r", "F.I.SH", "HEMIS ID", "Fakultet", "Yo'nalish", "Telefon", "Kirgan sana"]
    ws.append(headers)
    
    # Style headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        
    for i, (student, joined_at) in enumerate(results, 1):
        joined_str = joined_at.strftime("%d.%m.%Y") if joined_at else ""
        ws.append([
            i,
            student.full_name,
            student.hemis_login or student.hemis_id or "",
            student.faculty_name or "",
            student.specialty_name or "",
            student.phone or "",
            joined_str
        ])
        
    # Start columns width adjustment
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
        
    # Save to temp file
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    try:
        wb.save(path)
        os.close(fd)
        
        # Send file
        club = await session.get(Club, cid)
        filename = f"{club.name}_azolar.xlsx".replace(" ", "_")
        
        file = FSInputFile(path, filename=filename)
        await call.message.answer_document(file, caption=f"📊 <b>{club.name}</b> a'zolari ro'yxati.")
        
    finally:
        # Cleanup
        if os.path.exists(path):
            os.remove(path)

@router.callback_query(F.data.startswith("club_info:"))
async def cb_club_info(call: CallbackQuery, session: AsyncSession):
    cid = int(call.data.split(":")[1])
    club = await session.get(Club, cid)
    
    if not club:
        await call.answer("Klub topilmadi", show_alert=True)
        return
        
    info = (
        f"ℹ️ <b>Klub Ma'lumotlari</b>\n\n"
        f"🏷 <b>Nomi:</b> {club.name}\n"
        f"📝 <b>Tavsifi:</b> {club.description}\n"
        f"🔗 <b>Link:</b> {club.channel_link or 'Mavjud emas'}\n"
        f"👤 <b>Sardor (Siz):</b> O'zingiz\n\n"
        "<i>Ma'lumotlarni o'zgartirish uchun Admin bilan bog'laning.</i>"
    )
    
    await call.message.edit_text(info, reply_markup=get_back_inline_kb(f"leader_manage:{cid}"), parse_mode="HTML")

# --- BROADCAST ---
@router.callback_query(F.data.startswith("club_bc_start:"))
async def cb_bc_start(call: CallbackQuery, state: FSMContext):
    cid = int(call.data.split(":")[1])
    await state.update_data(bc_club_id=cid)
    await state.set_state(ClubStates.broadcasting_content)
    await call.message.edit_text("📢 <b>E'lon matnini (yoki rasm+matn) yuboring:</b>", reply_markup=get_back_inline_kb(f"leader_manage:{cid}"))

@router.message(ClubStates.broadcasting_content)
async def msg_bc_content(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    cid = data['bc_club_id']
    
    # Fetch members of THIS club
    from database.models import TgAccount, ClubMembership
    stmt = (
        select(TgAccount.telegram_id)
        .join(Student, TgAccount.student_id == Student.id)
        .join(ClubMembership, Student.id == ClubMembership.student_id)
        .where(ClubMembership.club_id == cid)
    )
    recipient_ids = (await session.execute(stmt)).scalars().all()
    
    sent_msg = await message.answer(f"⏳ <b>{len(recipient_ids)}</b> ta a'zoga yuborilmoqda...")
    
    success_count = 0
    blocked_count = 0
    
    for tid in recipient_ids:
        try:
            await message.copy_to(chat_id=tid)
            success_count += 1
        except Exception:
            blocked_count += 1
            
    await sent_msg.edit_text(
        f"✅ <b>E'lon yuborildi!</b>\n\n"
        f"Auditoriya: Klub A'zolari\n"
        f"Muvaffaqiyatli: {success_count}\n"
        f"Yetib bormadi (blok/o'chirilgan): {blocked_count}",
        reply_markup=get_back_inline_kb(f"leader_manage:{cid}")
    )
    await state.clear()

# --- CALENDAR EVENT ---
@router.callback_query(F.data.startswith("club_evt_start:"))
async def cb_evt_start(call: CallbackQuery, state: FSMContext):
    cid = int(call.data.split(":")[1])
    await state.update_data(evt_club_id=cid)
    await state.set_state(ClubStates.event_title)
    await call.message.edit_text("📅 <b>Tadbir nomini yozing:</b>\n(Masalan: Zakovat o'yini)", reply_markup=get_back_inline_kb(f"leader_manage:{cid}"))

@router.message(ClubStates.event_title)
async def msg_evt_title(message: Message, state: FSMContext):
    await state.update_data(evt_title=message.text)
    await state.set_state(ClubStates.event_date)
    await message.answer("📆 <b>Sana va vaqtni kiriting:</b>\n(Masalan: 20.12.2025 - 14:00)")

@router.message(ClubStates.event_date)
async def msg_evt_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    try:
        # Parse Format: DD.MM.YYYY - HH:MM
        # Input example: 20.12.2025 - 18:00
        dt = datetime.strptime(date_str, "%d.%m.%Y - %H:%M")
        
        # Convert to ICS format: YYYYMMDDTHHMMSS
        ics_date = dt.strftime("%Y%m%dT%H%M00")
        
        await state.update_data(evt_date_pretty=date_str, evt_date_ics=ics_date)
        await state.set_state(ClubStates.event_location)
        await message.answer("📍 <b>Manzilni kiriting:</b>\n(Masalan: 5-bino, Faollar zali)")
        
    except ValueError:
        await message.answer("❌ <b>Noto'g'ri format!</b>\nIltimos, namunadagidek kiriting:\n\n<code>20.12.2025 - 18:00</code>")

@router.message(ClubStates.event_location)
async def msg_evt_loc(message: Message, state: FSMContext, session: AsyncSession):
    loc = message.text
    data = await state.get_data()
    cid = data['evt_club_id']
    
    # Generate ICS Content
    ics_content = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//TalabaHamkorBot//EN\n"
        "BEGIN:VEVENT\n"
        f"SUMMARY:{data['evt_title']}\n"
        f"DTSTART:{data['evt_date_ics']}\n"
        f"LOCATION:{loc}\n"
        "DESCRIPTION:Universitet klubi tadbiri.\n"
        "END:VEVENT\n"
        "END:VCALENDAR"
    )
    
    from aiogram.types import BufferedInputFile
    file = BufferedInputFile(ics_content.encode('utf-8'), filename="tadbir.ics")
    
    # 1. Send confirmation to Leader
    sent_msg = await message.answer("⏳ Tadbir taqvimi yaratilmoqda va a'zolarga yuborilmoqda...")

    # 2. Fetch Members
    from database.models import TgAccount, ClubMembership
    stmt = (
        select(TgAccount.telegram_id)
        .join(Student, TgAccount.student_id == Student.id)
        .join(ClubMembership, Student.id == ClubMembership.student_id)
        .where(ClubMembership.club_id == cid)
    )
    recipient_ids = (await session.execute(stmt)).scalars().all()
    
    # 3. Broadcast File
    success_count = 0
    for tid in recipient_ids:
        try:
            # Re-create InputFile object or reuse? BufferedInputFile can be reused usually if bytes.
            # But safe way is sending by file_id after first send, or just sending bytes again.
            # send_document accepts BufferedInputFile.
            await message.bot.send_document(
                chat_id=tid,
                document=file,
                caption=f"📅 <b>Yangi Tadbir!</b>\n\nNom: {data['evt_title']}\nManzil: {loc}\nVaqt: {data['evt_date_pretty']}\n\n<i>Tadbirni kalendarga qo'shish uchun faylni oching.</i>",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception:
            pass
            
    await sent_msg.edit_text(
        f"✅ <b>Tadbir taqvimi yaratildi va {success_count} ta a'zoga yuborildi!</b>\n\n"
        f"Nom: {data['evt_title']}\nManzil: {loc}",
        reply_markup=get_back_inline_kb(f"leader_manage:{cid}")
    )
    await state.clear()

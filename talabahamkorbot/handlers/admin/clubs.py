
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from typing import Union
from database.db_connect import get_db
from database.models import User, Student, Club, StaffRole, Staff, ClubMembership
from models.states import ClubCreationStates, ClubEditStates
from handlers.auth import get_current_user

router = Router()

# Helper check for admin/owner
async def is_admin(user: Union[User, Staff, Student]) -> bool:
    if not hasattr(user, "role"):
        return False
        
    # If user is Staff, role is Enum or str
    # If user is User, role is str ("staff", "admin", etc)
    
    # Check if role is in ALLOWED_ROLES
    allowed_roles = [
        StaffRole.OWNER.value, 
        StaffRole.DEVELOPER.value,
        StaffRole.RAHBARIYAT.value,
        StaffRole.DEKANAT.value,
        StaffRole.YOSHLAR_PROREKTOR.value,
        StaffRole.YOSHLAR_YETAKCHISI.value # Also Allow Yetakchi
    ]
    
    # Handle Enum comparison by using value
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    
    return role_value in allowed_roles

@router.message(Command("add_club"))
async def cmd_add_club(message: types.Message, state: FSMContext, user_id: int = None):
    # Determine User ID
    tid = user_id or message.from_user.id
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"cmd_add_club triggered. tid={tid}, state={await state.get_state()}")
    
    # Check Admin
    from database.db_connect import get_db
    async for session in get_db():
        user = await get_current_user(tid, session)
        if not user or not await is_admin(user):
            if isinstance(message, types.Message):
                await message.answer("⚠️ Faqat adminlar klub qo'sha oladi.")
            return
        break
    
    # Create Cancel KB
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="club_create_cancel")]
    ])
    
    await state.set_state(ClubCreationStates.waiting_name)
    if isinstance(message, types.Message):
        if message.from_user.is_bot:
            await message.edit_text("📝 Yangi klub nomini kiriting:", reply_markup=kb)
        else:
            await message.answer("📝 Yangi klub nomini kiriting:", reply_markup=kb)

@router.callback_query(F.data == "owner_clubs_menu")
async def cb_owner_clubs_menu(call: types.CallbackQuery, state: FSMContext):
    # Check Admin
    from database.db_connect import get_db
    async for session in get_db():
        user = await get_current_user(call.from_user.id, session)
        if not user or not await is_admin(user):
            return await call.answer("⚠️ Faqat adminlar!", show_alert=True)
        break
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Yangi klub qo'shish", callback_data="admin_add_club")],
        [types.InlineKeyboardButton(text="🎭 To'garaklar ro'yxati", callback_data="admin_view_clubs")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_menu")]
    ])
    
    await call.message.edit_text("🎭 <b>Klublarni boshqarish menyusi</b>\n\nQuyidagilardan birini tanlang:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_view_clubs")
async def cb_view_clubs(call: types.CallbackQuery):
    async for db in get_db():
        clubs = (await db.execute(select(Club))).scalars().all()
        break
    
    if not clubs:
        return await call.answer("Hozircha klublar yo'q.", show_alert=True)
        
    buttons = []
    for club in clubs:
        buttons.append([types.InlineKeyboardButton(text=f"🎭 {club.name}", callback_data=f"admin_view_club:{club.id}")])
    
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_clubs_menu")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await call.message.edit_text("🎭 <b>Mavjud to'garaklar ro'yxati:</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_view_club:"))
async def cb_view_club_detail(call: types.CallbackQuery):
    club_id = int(call.data.split(":")[1])
    async for db in get_db():
        club = await db.get(Club, club_id)
        if club and club.leader_student_id:
             await db.refresh(club, ["leader_student"])
        break
        
    if not club:
        return await call.answer("Klub topilmadi.", show_alert=True)
        
    leader_name = club.leader_student.full_name if club.leader_student else "Tayinlanmagan"
    
    desc = club.description or "Yo'q"
    link = club.channel_link or "Yo'q"
    text = (
        f"🎭 <b>Klub: {club.name}</b>\n\n"
        f"ℹ️ <b>Tavsif:</b> {desc}\n"
        f"🔗 <b>Link:</b> {link}\n"
        f"👤 <b>Sardor:</b> {leader_name}\n"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="📝 Tahrirlash", callback_data=f"admin_edit_club_menu:{club.id}"),
            types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"admin_delete_club_ask:{club.id}")
        ],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_view_clubs")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_add_club")
async def cb_admin_add_club(call: types.CallbackQuery, state: FSMContext):
     await cmd_add_club(call.message, state, user_id=call.from_user.id)
     await call.answer()

@router.message(ClubCreationStates.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"process_name reached. text={message.text}, state={await state.get_state()}")
    if not message.text:
        await message.answer("Iltimos, matn kiriting.")
        return
    
    await state.update_data(name=message.text)
    await message.answer("✅ Tushunarli.\n\nEndi to'garak haqida qisqacha tavsif (description) yozing:")
    await state.set_state(ClubCreationStates.waiting_description)

@router.message(ClubCreationStates.waiting_description)
async def process_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, matn kiriting.")
        return

    await state.update_data(description=message.text)
    await message.answer(
        "✅ Qabul qilindi.\n\n"
        "To'garakning Telegram kanali yoki guruhi linkini yuboring (yoki 'yo'q' deb yozing):"
    )
    await state.set_state(ClubCreationStates.waiting_channel_link)

@router.message(ClubCreationStates.waiting_channel_link)
async def process_link(message: types.Message, state: FSMContext):
    link = message.text
    if link and link.lower() in ['yo\'q', 'yoq', 'no', '-']:
        link = None
    
    await state.update_data(channel_link=link)
    await message.answer(
        "✅ Yaxshi.\n\n"
        "Endi to'garak SARDORI (Leader) bo'ladigan talabaning <b>HEMIS Loginini</b> (ID) kiriting:"
    )
    await state.set_state(ClubCreationStates.waiting_leader_hemis)

@router.message(ClubCreationStates.waiting_leader_hemis)
async def process_leader(message: types.Message, state: FSMContext):
    hemis_login = message.text.strip()
    
    async for db in get_db():
        # Check if student exists
        student = await db.scalar(select(Student).where(Student.hemis_login == hemis_login))
        
        if not student:
            await message.answer(
                f"❌ <b>{hemis_login}</b> logini bilan talaba topilmadi.\n"
                "Iltimos, to'g'ri login kiriting yoki bekor qilish uchun /cancel ni bosing."
            )
            return

        data = await state.get_data()
        
        # Summary
        link_text = data.get('channel_link') or "Yo'q"
        msg = (
            "📋 <b>Ma'lumotlarni tasdiqlaysizmi?</b>\n\n"
            f"🏷 <b>Nom:</b> {data['name']}\n"
            f"ℹ️ <b>Tavsif:</b> {data['description']}\n"
            f"🔗 <b>Link:</b> {link_text}\n"
            f"👤 <b>Sardor:</b> {student.full_name} ({hemis_login})\n"
        )
        
        await state.update_data(leader_student_id=student.id, leader_name=student.full_name)
        await message.answer(msg, reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="club_create_confirm"), 
                 types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="club_create_cancel")]
            ]
        ), parse_mode="HTML")
        await state.set_state(ClubCreationStates.confirm_creation)
        await state.set_state(ClubCreationStates.confirm_creation)

@router.callback_query(F.data == "club_create_cancel")
async def process_cancel_creation(call: types.CallbackQuery, state: FSMContext):
    """Generic cancel handler for any step of club creation"""
    current_state = await state.get_state()
    if current_state in [
        ClubCreationStates.waiting_name.state,
        ClubCreationStates.waiting_description.state,
        ClubCreationStates.waiting_channel_link.state,
        ClubCreationStates.waiting_leader_hemis.state,
        ClubCreationStates.confirm_creation.state
    ]:
        await state.clear()
        await call.answer("❌ Klub yaratish bekor qilindi.", show_alert=True)
        await cb_owner_clubs_menu(call, state)

@router.callback_query(ClubCreationStates.confirm_creation)
async def process_confirm(call: types.CallbackQuery, state: FSMContext):
    # Cancel handled by generic handler strictly speaking, but if state filter catches it first:
    if call.data == "club_create_cancel":
        await process_cancel_creation(call, state)
        return
        
    if call.data == "club_create_confirm":
        data = await state.get_data()
        
        async for db in get_db():
            try:
                new_club = Club(
                    name=data['name'],
                    description=data['description'],
                    channel_link=data.get('channel_link'),
                    leader_student_id=data['leader_student_id']
                    # icon and color can be default or added later
                )
                db.add(new_club)
                await db.commit()
                
                await state.clear()
                await call.answer(
                    f"✅ {data['name']} to'garagi muvaffaqiyatli yaratildi!",
                    show_alert=True
                )
                await cb_owner_clubs_menu(call, state)
            except Exception as e:
                await call.message.answer(f"❌ Xatolik yuz berdi: {e}")
                await state.clear()


# ============================================================
# EDIT / DELETE HANDLERS
# ============================================================

@router.callback_query(F.data.startswith("admin_delete_club_ask:"))
async def cb_delete_club_ask(call: types.CallbackQuery):
    club_id = int(call.data.split(":")[1])
    
    # Confirm
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗑 Ha, o'chirish", callback_data=f"admin_delete_club_confirm:{club_id}")],
        [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_view_club:{club_id}")]
    ])
    
    await call.message.edit_text(
        "⚠️ <b>Diqqat!</b>\n\n"
        "Siz haqiqatan ham ushbu klubni o'chirmoqchimisiz?\n"
        "Bu amalni ortga qaytarib bo'lmaydi va barcha a'zoliklar bekor qilinadi.",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_delete_club_confirm:"))
async def cb_delete_club_confirm(call: types.CallbackQuery):
    club_id = int(call.data.split(":")[1])
    
    import logging
    logger = logging.getLogger(__name__)
    try:
        async for db in get_db():
            club = await db.get(Club, club_id)
            if club:
                await db.delete(club)
                await db.commit()
                await call.answer("✅ Klub o'chirildi!", show_alert=True)
                await cb_view_clubs(call) # Go back to list
            else:
                await call.answer("❌ Klub topilmadi.", show_alert=True)
                await cb_view_clubs(call)
            break
    except Exception as e:
        logger.error(f"Error deleting club {club_id}: {e}", exc_info=True)
        await call.answer(f"❌ Xatolik: {e}", show_alert=True)

@router.callback_query(F.data.startswith("admin_edit_club_menu:"))
async def cb_edit_club_menu(call: types.CallbackQuery):
    club_id = int(call.data.split(":")[1])
    
    async for db in get_db():
        club = await db.get(Club, club_id)
        if not club:
            return await call.answer("Klub topilmadi.", show_alert=True)
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🏷 Nomini o'zgartirish", callback_data=f"admin_edit_field:name:{club_id}")],
            [types.InlineKeyboardButton(text="ℹ️ Tavsifni o'zgartirish", callback_data=f"admin_edit_field:desc:{club_id}")],
            [types.InlineKeyboardButton(text="🔗 Linkni o'zgartirish", callback_data=f"admin_edit_field:link:{club_id}")],
            [types.InlineKeyboardButton(text="👤 Rahbarni o'zgartirish", callback_data=f"admin_edit_field:leader:{club_id}")],
            [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_view_club:{club_id}")]
        ])
        
        await call.message.edit_text(
            f"📝 <b>{club.name}</b> ni tahrirlash.\nQaysi ma'lumotni o'zgartirmoqchisiz?", 
            reply_markup=kb, 
            parse_mode="HTML"
        )
        break

@router.callback_query(F.data.startswith("admin_edit_field:"))
async def cb_edit_field(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    field = parts[1]
    club_id = int(parts[2])
    
    await state.update_data(edit_club_id=club_id)
    
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_edit_club_menu:{club_id}")]
    ])
    
    if field == "name":
        await state.set_state(ClubEditStates.waiting_new_name)
        await call.message.edit_text("✍️ Yangi <b>nomni</b> kiriting:", reply_markup=markup, parse_mode="HTML")
    elif field == "desc":
        await state.set_state(ClubEditStates.waiting_new_desc)
        await call.message.edit_text("✍️ Yangi <b>tavsifni</b> kiriting:", reply_markup=markup, parse_mode="HTML")
    elif field == "link":
        await state.set_state(ClubEditStates.waiting_new_link)
        await call.message.edit_text("🔗 Yangi <b>Telegram linkini</b> yuboring (yoki '-' deb yozing o'chirish uchun):", reply_markup=markup, parse_mode="HTML")
    elif field == "leader":
        await state.set_state(ClubEditStates.waiting_new_leader)
        await call.message.edit_text("👤 Yangi sardorning <b>HEMIS ID</b> sini kiriting:", reply_markup=markup, parse_mode="HTML")

@router.message(ClubEditStates.waiting_new_name)
async def process_edit_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    club_id = data.get('edit_club_id')
    new_name = message.text
    
    async for db in get_db():
        club = await db.get(Club, club_id)
        if club:
            club.name = new_name
            await db.commit()
            await message.answer("✅ Nom o'zgartirildi!")
            
            # Show menu again
            # We need to manually trigger the menu logic or just send a new message with the menu
            # Sending new message is safer for Message handler
            await message.answer("Yana nimani o'zgartiramiz?", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Tahrirlash menyusi", callback_data=f"admin_edit_club_menu:{club_id}")]
            ]))
        else:
            await message.answer("❌ Klub topilmadi.")
        break
    await state.clear()

@router.message(ClubEditStates.waiting_new_desc)
async def process_edit_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    club_id = data.get('edit_club_id')
    
    async for db in get_db():
        club = await db.get(Club, club_id)
        if club:
            club.description = message.text
            await db.commit()
            await message.answer("✅ Tavsif o'zgartirildi!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Tahrirlash menyusi", callback_data=f"admin_edit_club_menu:{club_id}")]
            ]))
        break
    await state.clear()

@router.message(ClubEditStates.waiting_new_link)
async def process_edit_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    club_id = data.get('edit_club_id')
    link = message.text.strip()
    
    if link in ['-', 'yoq', 'no']:
        link = None
        
    async for db in get_db():
        club = await db.get(Club, club_id)
        if club:
            club.channel_link = link
            await db.commit()
            await message.answer("✅ Link o'zgartirildi!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Tahrirlash menyusi", callback_data=f"admin_edit_club_menu:{club_id}")]
            ]))
        break
    await state.clear()

@router.message(ClubEditStates.waiting_new_leader)
async def process_edit_leader(message: types.Message, state: FSMContext):
    data = await state.get_data()
    club_id = data.get('edit_club_id')
    hemis_login = message.text.strip()
    
    async for db in get_db():
        student = await db.scalar(select(Student).where(Student.hemis_login == hemis_login))
        
        if not student:
            await message.answer("❌ Talaba topilmadi. Qayta urinib ko'ring yoki bekor qiling.", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_edit_club_menu:{club_id}")]
            ]))
            return

        club = await db.get(Club, club_id)
        if club:
            club.leader_student_id = student.id
            await db.commit()
            await message.answer(f"✅ Yangi sardor tayinlandi: <b>{student.full_name}</b>", parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Tahrirlash menyusi", callback_data=f"admin_edit_club_menu:{club_id}")]
            ]))
        break
    await state.clear()

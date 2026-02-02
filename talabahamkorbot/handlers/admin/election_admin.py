import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Student, Election, ElectionCandidate, ElectionVote, University, Faculty
from keyboards.inline_kb import get_student_main_menu_kb # For back navigation if needed

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.election_service import ElectionService

router = Router()
logger = logging.getLogger(__name__)

class AdminElectionStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_candidate_student_id = State()
    waiting_for_candidate_campaign = State()
    waiting_for_candidate_photo = State()
    waiting_for_edit_candidate_photo = State()
    waiting_for_edit_candidate_text = State()

# ================================
# 🛠 Keyboards
# ================================

def get_admin_election_menu_kb(university_id: int = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🆕 Yangi saylov yaratish", callback_data="admin_create_election"))
    builder.row(InlineKeyboardButton(text="📝 Saylovlarni boshqarish", callback_data="admin_manage_elections"))
    
    if university_id:
        if isinstance(university_id, str) and university_id == "global":
             builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_menu"))
        else:
             builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"owner_view_uni:{university_id}")) # Back to Owner Uni View
    else:
        builder.row(InlineKeyboardButton(text="🏠 Bosh menyuga qaytish", callback_data="go_student_home"))
    return builder.as_markup()

def get_admin_election_manage_kb(election_id: int, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👥 Nomzodlar boshqaruvi", callback_data=f"admin_candidates:{election_id}"))
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data=f"admin_election_stats:{election_id}"),
        InlineKeyboardButton(text="🕵️ Audit", callback_data=f"admin_election_audit:{election_id}")
    )
    builder.row(InlineKeyboardButton(text="📄 EXCEL (CSV) Eksport", callback_data=f"admin_election_csv:{election_id}"))

    if status == "draft":
        builder.row(InlineKeyboardButton(text="🚀 Saylovni boshlash (Active)", callback_data=f"admin_start_election:{election_id}"))
    elif status == "active":
        builder.row(InlineKeyboardButton(text="🛑 Saylovni yakunlash (Finish)", callback_data=f"admin_stop_election:{election_id}"))
    
    builder.row(InlineKeyboardButton(text="❌ O'chirish", callback_data=f"admin_delete_election:{election_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_manage_elections"))
    return builder.as_markup()

def get_admin_candidates_kb(election_id: int, candidates: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cand in candidates:
        builder.row(InlineKeyboardButton(text=f"👤 {cand.student.full_name}", callback_data=f"admin_view_candidate:{cand.id}"))
    
    builder.row(InlineKeyboardButton(text="➕ Nomzod qo'shish", callback_data=f"admin_add_candidate:{election_id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_view_election:{election_id}"))
    return builder.as_markup()

@router.callback_query(F.data.startswith("admin_view_candidate:"))
async def admin_view_candidate(call: CallbackQuery, session: AsyncSession):
    cand_id = int(call.data.split(":")[1])
    cand = await session.execute(
        select(ElectionCandidate)
        .where(ElectionCandidate.id == cand_id)
        .options(selectinload(ElectionCandidate.student), selectinload(ElectionCandidate.faculty))
    )
    cand = cand.scalar()
    if not cand: return

    text = (
        f"👤 <b>Nomzod:</b> {cand.student.full_name}\n"
        f"🏛 <b>Fakultet:</b> {cand.faculty.name}\n\n"
        f"📝 <b>Dastur:</b>\n{cand.campaign_text or 'Kiritilmagan'}"
    )

    kb = InlineKeyboardBuilder()
    if cand.photo_id:
        kb.row(InlineKeyboardButton(text="🖼 Rasmni o'zgartirish", callback_data=f"admin_edit_cand_photo:{cand.id}"))
    else:
        kb.row(InlineKeyboardButton(text="🖼 Rasm qo'shish", callback_data=f"admin_edit_cand_photo:{cand.id}"))
    
    kb.row(InlineKeyboardButton(text="📝 Tavsifni tahrirlash", callback_data=f"admin_edit_cand_text:{cand.id}"))
    kb.row(InlineKeyboardButton(text="❌ Nomzodni o'chirish", callback_data=f"admin_delete_candidate:{cand.id}"))
    kb.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_candidates:{cand.election_id}"))
    
    # Send as photo if exists
    if cand.photo_id:
        try:
            await call.message.delete()
        except: pass
        await call.message.answer_photo(cand.photo_id, caption=text, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await admin_edit_msg(call, text, kb.as_markup())

@router.callback_query(F.data.startswith("admin_delete_candidate:"))
async def admin_delete_candidate(call: CallbackQuery, session: AsyncSession):
    cand_id = int(call.data.split(":")[1])
    cand = await session.get(ElectionCandidate, cand_id)
    if not cand: return
    
    election_id = cand.election_id
    await session.delete(cand)
    await session.commit()
    
    await call.answer("✅ Nomzod o'chirildi", show_alert=True)
    # Go back to candidates list
    stmt = select(ElectionCandidate).options(selectinload(ElectionCandidate.student)).where(ElectionCandidate.election_id == election_id)
    candidates = (await session.scalars(stmt)).all()
    await admin_edit_msg(call, "👥 <b>Nomzodlar ro'yxati:</b>", get_admin_candidates_kb(election_id, candidates))

# ================================
# 🛠 Helpers
# ================================

async def admin_edit_msg(call: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup):
    """
    Helper to edit message (text or caption) depending on message type.
    """
    try:
        if call.message.photo:
            await call.message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await call.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in admin_edit_msg: {e}")
        # Fallback: delete and send new
        try:
            await call.message.delete()
        except: pass
        await call.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

# ================================
# 🛠 Handlers
# ================================

@router.callback_query(F.data.startswith("admin_election_menu"))
async def admin_election_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    
    university_id = None
    if ":" in call.data:
        raw_id = call.data.split(":")[1]
        if raw_id == "global":
            university_id = "global"
        else:
            university_id = int(raw_id)
        await state.update_data(university_id=university_id)
    
    text = "⚙️ <b>Saylovni boshqarish paneli</b>\n\nBu yerda siz yangi saylovlar yaratishingiz, nomzodlarni boshqarishingiz va saylov holatlarini kuzatishingiz mumkin."
    
    kb = get_admin_election_menu_kb(university_id=university_id)
    
    # Entrance from Profile (Photo) -> Clear and Send Text
    if call.message.photo:
        try:
            await call.message.delete()
        except: pass
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await admin_edit_msg(call, text, kb)

@router.callback_query(F.data == "admin_create_election")
async def admin_create_election(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminElectionStates.waiting_for_title)
    kb = InlineKeyboardBuilder()
    data = await state.get_data()
    university_id = data.get('university_id')
    back_cb = f"admin_election_menu:{university_id}" if university_id else "admin_election_menu"
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data=back_cb))
    await admin_edit_msg(call, "📌 Saylov nomini kiriting (masalan: <i>Fakultet Sardori 2026</i>):", kb.as_markup())

@router.message(AdminElectionStates.waiting_for_title)
async def process_election_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminElectionStates.waiting_for_description)
    await message.answer("📝 Saylov haqida qisqacha tavsif (description) kiriting:")

@router.message(AdminElectionStates.waiting_for_description)
async def process_election_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminElectionStates.waiting_for_deadline)
    await message.answer("📅 Saylov tugash vaqtini kiriting (Format: <code>YYYY-MM-DD HH:MM</code>, masalan: <code>2026-02-15 18:00</code>):", parse_mode="HTML")

@router.message(AdminElectionStates.waiting_for_deadline)
async def process_election_deadline(message: Message, state: FSMContext, session: AsyncSession):
    try:
        deadline = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        data = await state.get_data()
        
        if not university_id or university_id == "global":
            # If global, owner must select a university or we can ask for code
            # For now, let's keep it simple: if global, they cannot just "create" without context.
            # But they might have set university_id during creation flow.
            # Let's check if they are Owner and university_id is missing
            if not university_id:
                from utils.student_utils import get_student_by_tg
                student = await get_student_by_tg(message.from_user.id, session)
                university_id = student.university_id if student else None
        
        if not university_id or university_id == "global":
            return await message.answer("❌ Universitet aniqlanmadi. Yangi saylov yaratish uchun avval '🏛 OTM va fakultetlar' bo'limidan universitetni tanlang.")

        election = Election(
            university_id=university_id,
            title=data['title'],
            description=data['description'],
            deadline=deadline,
            status="draft"
        )
        session.add(election)
        await session.commit()
        
        await message.answer(f"✅ Saylov muvaffaqiyatli yaratildi! (Status: Draft)\n\nID: {election.id}\nNomi: {election.title}", reply_markup=get_admin_election_menu_kb(university_id=data.get('university_id')))
        await state.set_state(None) # Clear state but keep data (university_id) for further use
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Iltimos, qaytadan kiriting (YYYY-MM-DD HH:MM):")

@router.callback_query(F.data == "admin_manage_elections")
async def admin_list_elections(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    university_id = data.get('university_id')
    
    if not university_id:
        from utils.student_utils import get_student_by_tg
        student = await get_student_by_tg(call.from_user.id, session)
        university_id = student.university_id if student else None
        
    if not university_id:
        return await call.answer("Universitet aniqlanmadi.", show_alert=True)
    
    if university_id == "global":
        # Show all elections for Owner
        stmt = select(Election).order_by(Election.created_at.desc()).limit(50)
    else:
        stmt = select(Election).where(Election.university_id == university_id).order_by(Election.created_at.desc())
        
    elections = (await session.scalars(stmt)).all()
    
    if not elections:
        return await call.answer("Biron bir saylov topilmadi.", show_alert=True)
    
    builder = InlineKeyboardBuilder()
    for e in elections:
        status_emoji = {"draft": "📝", "active": "🚀", "finished": "🛑"}.get(e.status, "❓")
        builder.row(InlineKeyboardButton(text=f"{status_emoji} {e.title}", callback_data=f"admin_view_election:{e.id}"))
    
    back_callback = f"admin_election_menu:{university_id}" if university_id else "admin_election_menu"
    builder.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback))
    
    await admin_edit_msg(call, "📋 <b>Mavjud saylovlar ro'yxati:</b>", builder.as_markup())

@router.callback_query(F.data.startswith("admin_view_election:"))
async def admin_view_election(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    election = await session.get(Election, election_id)
    
    if not election:
        return await call.answer("Saylov topilmadi", show_alert=True)
    
    deadline_str = election.deadline.strftime("%d.%m.%Y %H:%M") if election.deadline else "Belgilanmagan"
    text = (
        f"🆔 <b>Saylov ID: #{election.id}</b>\n"
        f"📌 <b>Nomi:</b> {election.title}\n"
        f"📊 <b>Holati:</b> {election.status.upper()}\n"
        f"⏰ <b>Deadline:</b> {deadline_str}\n\n"
        f"📝 <b>Tavsif:</b>\n{election.description}"
    )
    
    await admin_edit_msg(call, text, get_admin_election_manage_kb(election_id, election.status))

@router.callback_query(F.data.startswith("admin_start_election:"))
async def admin_start_election(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    election = await session.get(Election, election_id)
    election.status = "active"
    await session.commit()
    await call.answer("🚀 Saylov boshlandi!", show_alert=True)
    await admin_view_election(call, session)

@router.callback_query(F.data.startswith("admin_stop_election:"))
async def admin_stop_election(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    
    # Use Service to finish and broadcast
    await ElectionService.finish_election(election_id, session)
    
    await call.answer("🛑 Saylov yakunlandi va natijalar e'lon qilindi!", show_alert=True)
    await admin_view_election(call, session)

@router.callback_query(F.data.startswith("admin_delete_election:"))
async def admin_delete_confirm(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    election = await session.get(Election, election_id)
    if not election: return

    text = f"🚨 <b>DIQQAT!</b>\n\nSiz rostdan ham <b>\"{election.title}\"</b> saylovini o'chirib tashlamoqchimisiz?\n\nBu amalni qaytarib bo'lmaydi va barcha ovozlar o'chib ketadi!"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chirilsin", callback_data=f"admin_delete_election_confirm:{election_id}"),
            InlineKeyboardButton(text="❌ Yo'q, qolsin", callback_data=f"admin_view_election:{election_id}")
        ]
    ])
    
    await admin_edit_msg(call, text, kb)
    await call.answer()

@router.callback_query(F.data.startswith("admin_delete_election_confirm:"))
async def admin_delete_election_actual(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    election = await session.get(Election, election_id)
    if election:
        await session.delete(election)
        await session.commit()
    
    await call.answer("✅ Saylov muvaffaqiyatli o'chirildi", show_alert=True)
    await admin_list_elections(call, session)

# ================================
# 📝 Candidate Editing
# ================================

@router.callback_query(F.data.startswith("admin_edit_cand_photo:"))
async def admin_edit_cand_photo_start(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    cand_id = int(call.data.split(":")[1])
    await state.update_data(edit_cand_id=cand_id)
    await state.set_state(AdminElectionStates.waiting_for_edit_candidate_photo)
    await admin_edit_msg(call, "🖼 Nomzod uchun yangi rasm yuboring (yoki bekor qilish uchun /cancel):", None)
    await call.answer()

@router.message(AdminElectionStates.waiting_for_edit_candidate_photo)
async def process_edit_cand_photo(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("Tahrirlash bekor qilindi.", reply_markup=get_admin_election_menu_kb())
    
    if not message.photo:
        return await message.answer("Iltimos, rasm yuboring yoki /cancel bosing.")
    
    data = await state.get_data()
    university_id = data.get('university_id')
    
    cand = await session.get(ElectionCandidate, cand_id)
    if cand:
        cand.photo_id = message.photo[-1].file_id
        await session.commit()
    
    await state.set_state(None)
    await message.answer("✅ Nomzod rasmi yangilandi!")
    # We don't have a 'call' here to refresh the view easily, 
    # but we can send the admin back to the election overview
    await message.answer("Bosh menyu:", reply_markup=get_admin_election_menu_kb(university_id=university_id))

@router.callback_query(F.data.startswith("admin_edit_cand_text:"))
async def admin_edit_cand_text_start(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    cand_id = int(call.data.split(":")[1])
    await state.update_data(edit_cand_id=cand_id)
    await state.set_state(AdminElectionStates.waiting_for_edit_candidate_text)
    await admin_edit_msg(call, "📝 Nomzod uchun yangi saylovoldi dasturini kiriting (yoki /cancel):", None)
    await call.answer()

@router.message(AdminElectionStates.waiting_for_edit_candidate_text)
async def process_edit_cand_text(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("Tahrirlash bekor qilindi.", reply_markup=get_admin_election_menu_kb())
    
    if not message.text:
         return await message.answer("Iltimos, matn kiriting.")
         
    data = await state.get_data()
    university_id = data.get('university_id')
    
    cand = await session.get(ElectionCandidate, cand_id)
    if cand:
        cand.campaign_text = message.text
        await session.commit()
    
    await state.set_state(None)
    await message.answer("✅ Nomzod dasturi yangilandi!")
    await message.answer("Bosh menyu:", reply_markup=get_admin_election_menu_kb(university_id=university_id))

# ================================
# 👥 Candidates Management
# ================================

@router.callback_query(F.data.startswith("admin_candidates:"))
async def admin_manage_candidates(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    stmt = select(ElectionCandidate).options(selectinload(ElectionCandidate.student)).where(ElectionCandidate.election_id == election_id)
    candidates = (await session.scalars(stmt)).all()
    
    await admin_edit_msg(call, "👥 <b>Nomzodlar ro'yxati:</b>", get_admin_candidates_kb(election_id, candidates))

@router.callback_query(F.data.startswith("admin_add_candidate:"))
async def admin_add_candidate_start(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    await state.update_data(election_id=election_id)
    await state.set_state(AdminElectionStates.waiting_for_candidate_student_id)
    await admin_edit_msg(call, "👤 Nomzodning <b>HEMIS Login</b> (Personal ID) sini kiriting:", None)

@router.message(AdminElectionStates.waiting_for_candidate_student_id)
async def process_cand_student_id(message: Message, state: FSMContext, session: AsyncSession):
    hemis_login = message.text.strip()
    student = await session.scalar(select(Student).where(Student.hemis_login == hemis_login))
    
    if not student:
        return await message.answer("❌ Talaba topilmadi. Iltimos, HEMIS loginni to'g'ri kiriting:")
    
    await state.update_data(student_id=student.id, faculty_id=student.faculty_id)
    await state.set_state(AdminElectionStates.waiting_for_candidate_campaign)
    await message.answer(f"✅ Talaba: <b>{student.full_name}</b>\nFakultet: {student.faculty_name}\n\nEndi nomzodning saylovoldi dasturini (campaign text) kiriting:", parse_mode="HTML")

@router.message(AdminElectionStates.waiting_for_candidate_campaign)
async def process_cand_campaign(message: Message, state: FSMContext):
    await state.update_data(campaign_text=message.text)
    await state.set_state(AdminElectionStates.waiting_for_candidate_photo)
    await message.answer("🖼 Nomzod rasmini yuboring (yoki /skip bosing):")

@router.message(AdminElectionStates.waiting_for_candidate_photo)
async def process_cand_photo(message: Message, state: FSMContext, session: AsyncSession):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text == "/skip":
        pass
    else:
        return await message.answer("Iltimos rasm yuboring yoki /skip tugmasini bosing.")

    data = await state.get_data()
    
    # Check if candidate already exists in this election
    existing = await session.scalar(
        select(ElectionCandidate).where(
            and_(ElectionCandidate.election_id == data['election_id'], ElectionCandidate.student_id == data['student_id'])
        )
    )
    
    if existing:
        data = await state.get_data()
        university_id = data.get('university_id')
        await state.set_state(None)
        return await message.answer("❌ Bu talaba allaqachon nomzod sifatida qo'shilgan.", reply_markup=get_admin_election_menu_kb(university_id=university_id))

    candidate = ElectionCandidate(
        election_id=data['election_id'],
        student_id=data['student_id'],
        faculty_id=data['faculty_id'],
        campaign_text=data['campaign_text'],
        photo_id=photo_id
    )
    session.add(candidate)
    await session.commit()
    
    university_id = data.get('university_id')
    await state.set_state(None)
    await message.answer("✅ Nomzod muvaffaqiyatli qo'shildi!", reply_markup=get_admin_election_menu_kb(university_id=university_id))
@router.callback_query(F.data.startswith("admin_election_stats:"))
async def admin_election_stats(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    election = await session.get(Election, election_id)
    if not election: return

    # Count votes per candidate
    results = await session.execute(
        select(ElectionCandidate, func.count(ElectionVote.id))
        .join(ElectionVote, ElectionCandidate.id == ElectionVote.candidate_id, isouter=True)
        .where(ElectionCandidate.election_id == election_id)
        .group_by(ElectionCandidate.id)
        .options(selectinload(ElectionCandidate.student))
    )
    
    total_votes = await session.scalar(select(func.count(ElectionVote.id)).where(ElectionVote.election_id == election_id))
    
    text = f"📊 <b>Saylov statistikasi:</b>\n{election.title}\n\n"
    text += f"🗳 Jami ovozlar: <b>{total_votes}</b>\n\n"
    
    for cand, count in results:
        perc = (count / total_votes * 100) if total_votes > 0 else 0
        text += f"👤 {cand.student.full_name}: <b>{count} ta</b> ({perc:.1f}%)\n"
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_view_election:{election_id}"))
    await admin_edit_msg(call, text, kb.as_markup())

@router.callback_query(F.data.startswith("admin_election_audit:"))
async def admin_election_audit(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    
    # Get last 20 votes for audit
    votes = await session.execute(
        select(ElectionVote)
        .where(ElectionVote.election_id == election_id)
        .order_by(ElectionVote.created_at.desc())
        .limit(20)
        .options(selectinload(ElectionVote.voter), selectinload(ElectionVote.candidate).selectinload(ElectionCandidate.student))
    )
    
    text = "🕵️ <b>Oxirgi 20 ta ovoz:</b>\n\n"
    for v in votes.scalars():
        v_time = v.created_at.strftime("%H:%M:%S")
        text += f"• {v_time} | {v.voter.hemis_login} -> {v.candidate.student.full_name}\n"
    
    if not text.strip():
        text = "Hozircha ovozlar yo'q."

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"admin_election_audit:{election_id}"))
    kb.row(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"admin_view_election:{election_id}"))
    await admin_edit_msg(call, text, kb.as_markup())

@router.callback_query(F.data.startswith("admin_election_csv:"))
async def admin_election_csv(call: CallbackQuery, session: AsyncSession):
    election_id = int(call.data.split(":")[1])
    election = await session.get(Election, election_id)
    
    import csv
    import io
    from aiogram.types import BufferedInputFile

    votes = await session.execute(
        select(ElectionVote)
        .where(ElectionVote.election_id == election_id)
        .options(selectinload(ElectionVote.voter), selectinload(ElectionVote.candidate).selectinload(ElectionCandidate.student))
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Vaqt", "HEMIS Login", "F.I.SH", "Kimga ovoz berdi"])
    
    for v in votes.scalars():
        writer.writerow([
            v.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            v.voter.hemis_login,
            v.voter.full_name,
            v.candidate.student.full_name
        ])
    
    file_content = output.getvalue().encode('utf-8-sig') # with BOM for Excel
    document = BufferedInputFile(file_content, filename=f"election_{election_id}_results.csv")
    
    await call.message.answer_document(document, caption=f"📄 {election.title} saylov natijalari (CSV formatda, Excelda ochiladi)")
    await call.answer()

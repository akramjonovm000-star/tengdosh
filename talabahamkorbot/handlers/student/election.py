import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database.models import Student, Election, ElectionCandidate, ElectionVote, TgAccount
from keyboards.inline_kb import get_election_candidates_kb, get_candidate_detail_kb

router = Router()
logger = logging.getLogger(__name__)

async def get_student_from_tg(user_id: int, session: AsyncSession) -> Student | None:
    tg = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == user_id)
    )
    if not tg or not tg.student_id:
        return None
    return await session.get(Student, tg.student_id)

@router.callback_query(F.data.in_({"student_election", "student_election:profile"}))
async def show_election_main(call: CallbackQuery, session: AsyncSession):
    """
    Saylovning asosiy oynasi: Saylov haqida ma'lumot va nomzodlar ro'yxati.
    """
    student = await get_student_from_tg(call.from_user.id, session)
    if not student:
        return await call.answer("Talaba ma'lumotlari topilmadi.", show_alert=True)

    # Universitetdagi faol saylovni qidiramiz
    stmt = select(Election).where(
        and_(
            Election.university_id == student.university_id, 
            Election.status == "active"
        )
    ).order_by(Election.created_at.desc())
    
    election = await session.scalar(stmt)
    if not election:
        return await call.answer("Hozirda faol saylovlar mavjud emas.", show_alert=True)

    # Deadline tekshiruvi
    if election.deadline and election.deadline < datetime.utcnow():
        return await call.answer("Saylov vaqti tugagan.", show_alert=True)

    # Faqat talabaning fakultetidagi nomzodlarni olamiz
    cand_stmt = select(ElectionCandidate).options(
        selectinload(ElectionCandidate.student)
    ).where(
        and_(
            ElectionCandidate.election_id == election.id,
            ElectionCandidate.faculty_id == student.faculty_id
        )
    ).order_by(ElectionCandidate.order)
    
    candidates = (await session.scalars(cand_stmt)).all()
    
    is_from_profile = call.data == "student_election:profile"
    back_callback = "student_profile" if is_from_profile else "go_student_home"
    
    if not candidates:
        text = (
            f"🗳 <b>{election.title}</b>\n\n"
            f"{election.description or ''}\n\n"
            f"⚠️ Sizning fakultetingizda hozircha nomzodlar yo'q."
        )
    else:
        text = (
            f"🗳 <b>{election.title}</b>\n\n"
            f"{election.description or ''}\n\n"
            f"👥 <b>Fakultet nomzodlari:</b>"
        )
    
    kb = get_election_candidates_kb(candidates, back_callback=back_callback)
    
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        # Handle photo-to-text or other edit errors
        await call.message.delete()
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("election_cand:"))
async def view_candidate_detail(call: CallbackQuery, session: AsyncSession):
    """
    Nomzodning saylovoldi dasturini ko'rish.
    """
    parts = call.data.split(":")
    cand_id = int(parts[1])
    is_profile = parts[2] == "profile" if len(parts) > 2 else False
    back_callback = "student_election:profile" if is_profile else "student_election"
    
    candidate = await session.get(ElectionCandidate, cand_id, options=[selectinload(ElectionCandidate.student)])
    
    if not candidate:
        return await call.answer("Nomzod topilmadi.", show_alert=True)
    
    student = await get_student_from_tg(call.from_user.id, session)
    
    # Ovoz berganligini tekshirish
    vote_stmt = select(ElectionVote).where(
        and_(ElectionVote.election_id == candidate.election_id, ElectionVote.voter_id == student.id)
    )
    has_voted = await session.scalar(vote_stmt) is not None

    text = (
        f"👤 <b>Nomzod:</b> {candidate.student.full_name}\n\n"
        f"📝 <b>Saylovoldi dasturi:</b>\n"
        f"{candidate.campaign_text or 'Dastur mavjud emas.'}\n\n"
        f"{'✅ Siz ovoz bergansiz.' if has_voted else '👇 Ovoz berish tugmasini bosishingiz mumkin.'}"
    )
    
    kb = get_candidate_detail_kb(cand_id, can_vote=not has_voted, back_callback=back_callback)
    
    
    if candidate.photo_id:
        try:
            # OPTIMIZATION: If already a photo message, just edit caption!
            if call.message.photo:
                await call.message.edit_caption(
                    caption=text[:1024],
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                 # If it was text, we must delete and send photo
                 await call.message.delete()
                 await call.message.answer_photo(
                    photo=candidate.photo_id,
                    caption=text[:1024],
                    reply_markup=kb,
                    parse_mode="HTML"
                 )
        except Exception as e:
            # Fallback (e.g. caption too long or other error)
            try:
                await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
            except: pass
    else:
        try:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            try:
                await call.message.delete()
            except: pass
            await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("election_vote:"))
async def process_election_vote(call: CallbackQuery, session: AsyncSession):
    """
    Ovoz berish jarayoni.
    """
    parts = call.data.split(":")
    cand_id = int(parts[1])
    is_profile = parts[2] == "profile" if len(parts) > 2 else False
    
    candidate = await session.get(ElectionCandidate, cand_id)
    
    if not candidate:
        return await call.answer("Nomzod topilmadi.", show_alert=True)
        
    student = await get_student_from_tg(call.from_user.id, session)
    
    # Qayta tekshirish (poyga holatlarini oldini olish uchun)
    vote_stmt = select(ElectionVote).where(
        and_(ElectionVote.election_id == candidate.election_id, ElectionVote.voter_id == student.id)
    )
    if await session.scalar(vote_stmt):
        return await call.answer("Siz allaqachon ovoz bergansiz!", show_alert=True)

    # Ovozni yozish
    vote = ElectionVote(
        election_id=candidate.election_id,
        voter_id=student.id,
        candidate_id=candidate.id
    )
    session.add(vote)
    await session.commit()
    
    await call.answer("✅ Ovozingiz qabul qilindi!", show_alert=True)
    
    # Sahifani yangilash - call data formatini o'zgartiramizki view_candidate_detail tushunsin
    state_suffix = ":profile" if is_profile else ":main"
    call.data = f"election_cand:{cand_id}{state_suffix}"
    await view_candidate_detail(call, session)

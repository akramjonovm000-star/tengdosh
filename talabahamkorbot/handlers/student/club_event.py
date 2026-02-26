from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models.states import ClubEventActivityState
from database.models import (
    ClubEvent, ClubEventParticipant, UserActivity, UserActivityImage
)

router = Router()
logger = logging.getLogger(__name__)

@router.message(ClubEventActivityState.waiting_for_photo, F.photo | F.document | F.text)
async def process_club_event_photo(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    event_id = data.get("club_event_id")
    uploaded_photos = data.get("uploaded_photos", [])
    
    if message.text == "✅ Yakunlash":
        # Process the uploaded photos and mark activity
        if not uploaded_photos:
            await message.answer("Siz hech qanday rasm yuklamadingiz. Kamida bitta rasm yuklang.")
            return
            
        ev = await session.get(ClubEvent, event_id)
        if not ev:
            await message.answer("Tadbir o'chirilgan yoki topilmadi.", reply_markup=ReplyKeyboardRemove())
            await state.clear()
            return
            
        # Get all attended participants
        parts = await session.scalars(
            select(ClubEventParticipant)
            .where(
                ClubEventParticipant.event_id == event_id,
                ClubEventParticipant.attendance_status == "attended"
            )
        )
        parts_list = parts.all()
        
        if not parts_list:
            await message.answer("Tadbirda 'Qatnashdi' (attended) deb belgilangan hech qanday ishtirokchi yo'q. Avval mobil ilovadan qatnashganlarni belgilang.", reply_markup=ReplyKeyboardRemove())
            await state.clear()
            return
            
        # Create UserActivity for each
        created_count = 0
        from datetime import datetime
        
        for p in parts_list:
            # Check if this student already has activity for this event to avoid duplicates
            existing = await session.scalar(
                select(UserActivity).where(
                    UserActivity.student_id == p.student_id,
                    UserActivity.name == ev.title[:255],
                    UserActivity.category == "Tadbir"
                )
            )
            if existing:
                continue
                
            desc = ev.description or ''
            activity = UserActivity(
                student_id=p.student_id,
                category="Tadbir",
                name=ev.title[:255],
                description=f"Klub tadbirida faol ishtirok etildi. {desc[:100]}",
                date=ev.event_date.strftime("%Y-%m-%d") if ev.event_date else datetime.utcnow().strftime("%Y-%m-%d"),
                status="approved" # Auto approve!
            )
            session.add(activity)
            await session.commit() # commit to get ID
            await session.refresh(activity)
            
            # Add photos to each activity
            for photo_id in uploaded_photos:
                img = UserActivityImage(
                    activity_id=activity.id,
                    file_id=photo_id
                )
                session.add(img)
            created_count += 1
            
        if created_count > 0:
            await session.commit()
            await message.answer(
                f"✅ <b>Muvaffaqiyatli!</b>\n\n"
                f"Jami {created_count} ta talabaga \"Ijtimoiy faollik\" (Tadbir) avtomatik tasdiqlandi va rasmlar biriktirildi.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer("✅ Barcha qatnashchilarga avval faollik qo'shib bo'lingan ekan.", reply_markup=ReplyKeyboardRemove())
            
        await state.clear()
        return

    # Cancel command check
    if message.text == "/cancel" or (message.text and message.text.lower() == "bekor qilish"):
        await state.clear()
        await message.answer("Tadbir faolligini yakunlash bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        return

    # Handle photo upload
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and getattr(message.document, 'mime_type', '').startswith('image/'):
        file_id = message.document.file_id
        
    if not file_id:
        await message.answer("Iltimos faqat rasm yuboring, yoki tugatish uchun \"✅ Yakunlash\" tugmasini bosing.")
        return
        
    if len(uploaded_photos) >= 5:
        await message.answer("Siz maksimal 5 ta rasm yuklab bo'ldingiz. Iltimos \"✅ Yakunlash\" tugmasini bosing.")
        return
        
    uploaded_photos.append(file_id)
    await state.update_data(uploaded_photos=uploaded_photos)
    
    await message.answer(f"✅ Rasm qabul qilindi ({len(uploaded_photos)}/5).\n\nYana rasm yuborishingiz yoki jarayonni yakunlashingiz mumkin.")

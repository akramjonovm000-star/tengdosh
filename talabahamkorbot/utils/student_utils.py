from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TgAccount, Student, StudentNotification
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import re

def format_name(full_name: str) -> str:
    """Formats full name to 'First Last' (Sentence Case), removing (...) parts."""
    if not full_name: return "Noma'lum"
    
    # Remove text inside parentheses (e.g., patronymic)
    clean_name = re.sub(r'\s*\(.*?\)', '', full_name).strip()
    
    parts = clean_name.split()
    if len(parts) >= 2:
        # Assume DB stores "Last First" (Hemis default)
        # We want "First Last"
        return f"{parts[1].capitalize()} {parts[0].capitalize()}"
        
    return clean_name.title()

from sqlalchemy.orm import selectinload

async def get_student_by_tg(telegram_id: int, session: AsyncSession) -> Student:
    """
    Retrieves student by telegram ID and performs auto-revocation if expired.
    Matches logic in api/dependencies.py.
    """
    tg_acc = await session.scalar(
        select(TgAccount).where(TgAccount.telegram_id == telegram_id)
        .options(selectinload(TgAccount.student).selectinload(Student.university),
                 selectinload(TgAccount.student).selectinload(Student.faculty))
    )
    if not tg_acc or not tg_acc.student:
        return None
    
    student = tg_acc.student
    if not student:
        return None

    # --- AUTO-EXPIRATION CHECK ---
    if student.is_premium and student.premium_expiry:
        if student.premium_expiry < datetime.utcnow():
            student.is_premium = False
            
            # Add notification for expired premium
            notif = StudentNotification(
                student_id=student.id,
                title="⚠️ Premium muddati tugadi",
                body="Sizning Premium obunangiz muddati tugadi. Imkoniyatlarni qayta tiklash uchun hisobingizni to'ldiring.",
                type="alert"
            )
            session.add(notif)
            await session.commit()
            
    return student

async def check_premium_access(tg_id: int, session: AsyncSession, feature_name: str = "Ushbu funksiya"):
    """
    Unified check for premium access.
    Returns (is_allowed, response_text, reply_markup)
    """
    acc = await session.scalar(select(TgAccount).where(TgAccount.telegram_id == tg_id))
    if not acc:
        print(f"PREMIUM_CHECK: {tg_id} -> No Account")
        return False, "Hisob topilmadi.", None
        
    role = acc.current_role
    print(f"PREMIUM_CHECK: {tg_id} -> Role: {role}")
    
    # 1. ALLOW OWNER (Admin Privilege)
    if role == "owner":
        print(f"PREMIUM_CHECK: {tg_id} -> Allowed (Owner)")
        return True, None, None

    # 2. CHECK STUDENT
    if role == "student":
        student = await get_student_by_tg(tg_id, session)
        if not student:
            print(f"PREMIUM_CHECK: {tg_id} -> Student not found")
            return False, "⚠️ <b>Talaba ma'lumotlari topilmadi!</b>\n\nIltimos, HEMIS orqali tizimga qayta kiring.", None
            
        print(f"PREMIUM_CHECK: {tg_id} -> Student Premium: {student.is_premium}")
        if student.is_premium:
            return True, None, None
            
        # Not Premium (Student) -> Show Button
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Premiumga o'tish", callback_data="student_premium_menu")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_student_home")]
        ])
        text = (
            f"⚠️ {feature_name} faqat Premium foydalanuvchilar uchun!\n\n"
            "Ushbu funksiyadan foydalanish uchun Premium obunani faollashtiring."
        )
        return False, text, kb

    # 3. GENERIC BLOCK FOR OTHERS (Staff, etc.)
    # Treated as "Not Premium"
    print(f"PREMIUM_CHECK: {tg_id} -> Denied (Role: {role} - Not Premium)")
    
    text = (
        f"⚠️ {feature_name} faqat Premium foydalanuvchilar uchun!\n\n"
        "Sizning hisobingizda Premium obuna mavjud emas."
    )
    # No button for staff/others as they don't have a buy flow yet
    return False, text, None

def get_premium_label(student: Student) -> str:
    """Returns a string indicating premium status."""
    if not student:
        return "💡 Oddiy"
    if student.is_premium:
        return "💎 PREMIUM"
    return "💡 Oddiy"

async def get_election_info(student: Student, session: AsyncSession) -> tuple[bool, bool]:
    """
    Returns (is_election_admin, has_active_election) for a given student.
    """
    if not student:
        return False, False
        
    is_election_admin = student.is_election_admin
    has_active_election = False
    
    # Check for active election
    # Optimization: We only check if the student belongs to a university
    if student.university_id:
        from database.models import Election
        from sqlalchemy import and_
        
        active_election = await session.scalar(
            select(Election).where(
                and_(
                    Election.university_id == student.university_id,
                    Election.status == "active"
                )
            ).order_by(Election.created_at.desc())
        )
        if active_election:
            if not active_election.deadline or active_election.deadline > datetime.utcnow():
                has_active_election = True
                
    return is_election_admin, has_active_election

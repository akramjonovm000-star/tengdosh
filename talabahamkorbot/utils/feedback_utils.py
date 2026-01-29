
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models import StudentFeedback, FeedbackReply, Staff

async def get_feedback_thread_text(feedback_id: int, session: AsyncSession) -> str:
    """
    Berilgan feedback asosida butun suhbat tarixini xronologik tartibda qaytaradi.
    Returns: Formatted string of the conversation history.
    """
    
    # 1. Asl (Root) feedbackni topish
    root_feedback = await session.get(StudentFeedback, feedback_id)
    if not root_feedback:
        return "❌ Murojaat topilmadi."

    # Agar bu child bo'lsa, uning parentini olamiz
    if root_feedback.parent_id:
        root_feedback = await session.get(StudentFeedback, root_feedback.parent_id)
        if not root_feedback:
             return "❌ Asosiy murojaat topilmadi."

    root_id = root_feedback.id

    # 2. Barcha tegishli feedbacklarni olish (Root + Children)
    stmt_feedbacks = select(StudentFeedback).where(
        or_(StudentFeedback.id == root_id, StudentFeedback.parent_id == root_id)
    ).order_by(StudentFeedback.created_at)
    
    feedbacks_result = await session.execute(stmt_feedbacks)
    all_feedbacks = feedbacks_result.scalars().all()

    # 3. Barcha javoblarni olish (Staff bilan birga)
    feedback_ids = [f.id for f in all_feedbacks]
    
    stmt_replies = select(FeedbackReply).options(
        selectinload(FeedbackReply.staff)
    ).where(
        FeedbackReply.feedback_id.in_(feedback_ids)
    ).order_by(FeedbackReply.created_at)
    
    replies_result = await session.execute(stmt_replies)
    all_replies = replies_result.scalars().all()
    
    # 4. Birlashirish va Saralash
    timeline = []
    
    for fb in all_feedbacks:
        timeline.append({"type": "student", "obj": fb, "date": fb.created_at})
        
    for rep in all_replies:
        timeline.append({"type": "staff", "obj": rep, "date": rep.created_at})
    
    timeline.sort(key=lambda x: x["date"])
    
    # 5. Matn shakllantirish
    text_parts = []
    
    for item in timeline:
        dt_str = item["date"].strftime("%d.%m.%Y %H:%M")
        
        if item["type"] == "student":
            fb: StudentFeedback = item["obj"]
            sender = "🕵️‍♂️ Anonim Talaba" if fb.is_anonymous else "👤 Talaba"
            
            if fb.id == root_id:
                # Asosiy murojaat (Headerda bari bor, shuning uchun qisqa)
                content = f"<b>{sender}:</b>\n{fb.text or '[Media fayl]'}"
            else:
                prefix = "QAYTA MUROJAAT"
                content = f"--- {dt_str} | {prefix} (ID: {fb.id}) ---\n<b>{sender}:</b>\n{fb.text or '[Media fayl]'}"
            
            text_parts.append(content)
            
        elif item["type"] == "staff":
            rep: FeedbackReply = item["obj"]
            if rep.staff:
                if rep.staff.position:
                    role_display = rep.staff.position
                else:
                    role_display = rep.staff.role.capitalize()
                
                name = rep.staff.full_name
            else:
                role_display = "Xodim"
                name = "(Topilmadi)"
            
            content = f"--- {dt_str} | JAVOB ---\n<b>👮‍♂️ {role_display} {name}:</b>\n{rep.text}"
            text_parts.append(content)

    return "\n\n".join(text_parts)

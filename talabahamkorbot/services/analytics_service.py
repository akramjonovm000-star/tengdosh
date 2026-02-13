from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Student, University, Faculty, UserAppeal, StudentFeedback, UserActivity, StudentDocument, ChoyxonaPost, ChoyxonaComment, AiMessage
from datetime import datetime, timedelta

async def get_ai_analytics_summary(session: AsyncSession) -> str:
    """
    Computes a text summary of key database statistics for high-level AI context.
    Includes:
    - Total Users/Students
    - Users by University
    - Users by Faculty
    - Recent Appeals count
    """
    
    # 1. TOTAL COUNTS
    user_count = await session.scalar(select(func.count(User.id)))
    student_count = await session.scalar(select(func.count(Student.id)))
    
    # 2. UNIVERSITY STATS
    # Top 5 universities by user count
    uni_stm = (
        select(User.university_name, func.count(User.id).label('cnt'))
        .group_by(User.university_name)
        .order_by(desc('cnt'))
        .limit(5)
    )
    uni_res = await session.execute(uni_stm)
    uni_stats = "\n".join([f"- {row.university_name or 'Noma`lum'}: {row.cnt}" for row in uni_res])

    # 3. FACULTY STATS (Top 10 from Students Table)
    fac_stm = (
        select(Student.faculty_name, func.count(Student.id).label('cnt'))
        .group_by(Student.faculty_name)
        .order_by(desc('cnt'))
        .limit(10)
    )
    fac_res = await session.execute(fac_stm)
    
    fac_lines = []
    for row in fac_res:
        name = row.faculty_name if row.faculty_name else "Fakulteti biriktirilmagan"
        if row.cnt > 0:
            fac_lines.append(f"- {name}: {row.cnt} nafar")
            
    fac_stats = "\n".join(fac_lines)

    # 4. APPEALS & FEEDBACK
    appeal_count = await session.scalar(select(func.count(UserAppeal.id)))
    feedback_count = await session.scalar(select(func.count(StudentFeedback.id)))

    # 5. ACTIVITIES, DOCUMENTS, CERTIFICATES
    act_total = await session.scalar(select(func.count(UserActivity.id)))
    act_pending = await session.scalar(select(func.count(UserActivity.id)).where(UserActivity.status == 'pending'))
    act_approved = await session.scalar(select(func.count(UserActivity.id)).where(UserActivity.status == 'approved'))
    
    doc_total = await session.scalar(select(func.count(StudentDocument.id)).where(StudentDocument.file_type == 'document'))
    cert_total = await session.scalar(select(func.count(StudentDocument.id)).where(StudentDocument.file_type == 'certificate'))

    # Get active students count (active within last 30 days or similar - keeping simple for now)
    # Let's count premium students
    premium_count = await session.scalar(select(func.count(Student.id)).where(Student.is_premium == True))
    
    # Format for AI - CLEAN & PRECISE
    summary = (
        f"--- TIZIMNING REAL VAQTIDAGI STATISTIKASI ({func.now()}) ---\n"
        f"👥 Jami foydalanuvchilar: {user_count} nafar\n"
        f"🎓 Jami talabalar: {student_count} nafar (shundan {premium_count} tasi Premium)\n\n"
        f"🏛 FAKULTETLAR KESIMI (Talabalar bo'yicha):\n{fac_stats}\n\n"
        f"🏃‍♂️ FAOLLIKLAR:\n"
        f"- Jami: {act_total} ta\n"
        f"- Tasdiqlangan: {act_approved} ta\n"
        f"- Kutilmoqda: {act_pending} ta\n\n"
        f"📂 HUJJATLAR: {doc_total} ta\n"
        f"📜 SERTIFIKATLAR: {cert_total} ta\n\n"
        f"📩 Murojaatlar: {appeal_count} ta\n"
        f"⭐️ Fikrlar: {feedback_count} ta\n"
        f"---"
    )
    
    return summary

async def get_management_analytics(session: AsyncSession) -> dict:
    """
    Computes detailed analytics for the Management Dashboard.
    """
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # 1. TALABALAR UMUMIY HOLATI
    # Total Students
    total_students = await session.scalar(select(func.count(Student.id)))
    # Premium (Active proxy)
    premium_students = await session.scalar(select(func.count(Student.id)).where(Student.is_premium == True))
    # Active in last 24h (UserActivity as proxy)
    active_24h = await session.scalar(select(func.count(UserActivity.id)).where(UserActivity.created_at >= last_24h))
    
    # 2. TALABALAR KAYFIYATI (SENTIMENT)
    recent_posts_count = await session.scalar(select(func.count(ChoyxonaPost.id)).where(ChoyxonaPost.created_at >= last_7d))
    recent_comments_count = await session.scalar(select(func.count(ChoyxonaComment.id)).where(ChoyxonaComment.created_at >= last_7d))
    recent_ai_chats = await session.scalar(select(func.count(AiMessage.id)).where(AiMessage.created_at >= last_7d))
    
    # Sentiment Heuristic (Simple Mock)
    sentiment_score = 50 
    if recent_posts_count > 5: sentiment_score += 10
    if recent_comments_count > 10: sentiment_score += 10
    sentiment_score = min(100, sentiment_score)

    # 3. FAKULTETLAR STATISTIKASI (Most Active)
    fac_activity_stmt = (
        select(Student.faculty_name, func.count(UserActivity.id).label('cnt'))
        .join(UserActivity, UserActivity.student_id == Student.id)
        .where(UserActivity.created_at >= last_30d)
        .group_by(Student.faculty_name)
        .order_by(desc('cnt'))
        .limit(5)
    )
    fac_act_res = await session.execute(fac_activity_stmt)
    top_faculties = [{"name": row.faculty_name or "Noma'lum", "count": row.cnt} for row in fac_act_res]
    
    # 4. ILOVA FAOLLIGI (DAU Proxy)
    actions_24h = (
        (active_24h or 0) + 
        (await session.scalar(select(func.count(ChoyxonaPost.id)).where(ChoyxonaPost.created_at >= last_24h)) or 0) +
        (await session.scalar(select(func.count(ChoyxonaComment.id)).where(ChoyxonaComment.created_at >= last_24h)) or 0) +
        (await session.scalar(select(func.count(AiMessage.id)).where(AiMessage.created_at >= last_24h)) or 0)
    )

    # 5. MUAMMOLAR VA XAVF (Most Appeals)
    risk_stmt = (
         select(Student.faculty_name, func.count(UserAppeal.id).label('cnt'))
        .join(UserAppeal, UserAppeal.student_id == Student.id)
        .where(UserAppeal.created_at >= last_30d)
        .group_by(Student.faculty_name)
        .order_by(desc('cnt'))
        .limit(3)
    )
    risk_res = await session.execute(risk_stmt)
    risk_faculties = [{"name": row.faculty_name or "Noma'lum", "count": row.cnt} for row in risk_res]

    return {
        "students": {
            "total": total_students,
            "active": premium_students, 
            "actions_24h": actions_24h
        },
        "sentiment": {
            "posts_7d": recent_posts_count,
            "comments_7d": recent_comments_count,
            "ai_chats_7d": recent_ai_chats,
            "score": sentiment_score
        },
        "faculties": top_faculties,
        "risks": risk_faculties
    }

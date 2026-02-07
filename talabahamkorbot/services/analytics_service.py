from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Student, University, Faculty, UserAppeal, StudentFeedback, UserActivity, UserDocument, UserCertificate

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
    
    doc_total = await session.scalar(select(func.count(UserDocument.id)))
    cert_total = await session.scalar(select(func.count(UserCertificate.id)))

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

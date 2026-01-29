"""
KPI Calculator Service for Tyutor Module
Calculates tyutor performance based on 5 metrics
"""

from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Staff, Student, TutorGroup,
    UserActivity, StudentFeedback,
    ParentContactLog, TyutorKPI
)


async def calculate_tyutor_kpi(
    tyutor_id: int,
    quarter: int,
    year: int,
    session: AsyncSession
) -> float:
    """
    Tyutor KPI hisoblash (100 ball tizimida)
    
    1. Talabalar qamrovi (30%)
    2. Muammo aniqlash (25%)
    3. Tadbir faolligi (20%)
    4. Ota-ona aloqasi (15%)
    5. Intizom (10%)
    """
    
    # Chorak sanalarini aniqlash
    start_date, end_date = get_quarter_dates(quarter, year)
    
    # 1. Talabalar qamrovi (30%)
    coverage_score = await calculate_coverage_score(tyutor_id, session)
    
    # 2. Muammo aniqlash (25%)
    risk_score = await calculate_risk_detection_score(
        tyutor_id, start_date, end_date, session
    )
    
    # 3. Tadbir faolligi (20%)
    activity_score = await calculate_activity_score(
        tyutor_id, start_date, end_date, session
    )
    
    # 4. Ota-ona aloqasi (15%)
    parent_score = await calculate_parent_contact_score(
        tyutor_id, start_date, end_date, session
    )
    
    # 5. Intizom (10%)
    discipline_score = await calculate_discipline_score(tyutor_id, session)
    
    # Umumiy KPI
    total_kpi = (
        coverage_score * 0.30 +
        risk_score * 0.25 +
        activity_score * 0.20 +
        parent_score * 0.15 +
        discipline_score * 0.10
    )
    
    # KPI ni saqlash
    await save_kpi(
        tyutor_id, quarter, year,
        coverage_score, risk_score, activity_score,
        parent_score, discipline_score, total_kpi,
        session
    )
    
    return total_kpi


async def calculate_coverage_score(tyutor_id: int, session: AsyncSession) -> float:
    """Talabalar qamrovi (30 ball)"""
    # Tyutor talabalarini olish
    result = await session.execute(
        select(func.count(Student.id))
        .join(TutorGroup, Student.group_number == TutorGroup.group_number)
        .where(TutorGroup.tutor_id == tyutor_id)
    )
    total_students = result.scalar() or 0
    
    if total_students == 0:
        return 0.0
    
    # Faol ishlar soni (feedback, activity, contact)
    # Har bir talaba bilan kamida 1 ta ish bo'lishi kerak
    # 100% qamrov = 30 ball
    
    # Soddalashtirilgan: har bir talaba uchun 1 ball
    # Keyinchalik murakkablashtirish mumkin
    return min(total_students / total_students * 30, 30.0)


async def calculate_risk_detection_score(
    tyutor_id: int,
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession
) -> float:
    """Muammo aniqlash (25 ball)"""
    # Tyutor talabalaridan kelgan feedbacklar
    result = await session.execute(
        select(func.count(StudentFeedback.id))
        .join(Student, StudentFeedback.student_id == Student.id)
        .join(TutorGroup, Student.group_number == TutorGroup.group_number)
        .where(
            TutorGroup.tutor_id == tyutor_id,
            StudentFeedback.created_at.between(start_date, end_date)
        )
    )
    feedback_count = result.scalar() or 0
    
    # Har 2 ta feedback = 5 ball (max 25)
    score = min((feedback_count / 2) * 5, 25.0)
    return score


async def calculate_activity_score(
    tyutor_id: int,
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession
) -> float:
    """Tadbir faolligi (20 ball)"""
    # Tyutor talabalarining faolliklari
    result = await session.execute(
        select(func.count(UserActivity.id))
        .join(Student, UserActivity.student_id == Student.id)
        .join(TutorGroup, Student.group_number == TutorGroup.group_number)
        .where(
            TutorGroup.tutor_id == tyutor_id,
            UserActivity.status == "approved",
            UserActivity.created_at.between(start_date, end_date)
        )
    )
    activity_count = result.scalar() or 0
    
    # Har 5 ta faollik = 4 ball (max 20)
    score = min((activity_count / 5) * 4, 20.0)
    return score


async def calculate_parent_contact_score(
    tyutor_id: int,
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession
) -> float:
    """Ota-ona aloqasi (15 ball)"""
    result = await session.execute(
        select(func.count(ParentContactLog.id))
        .where(
            ParentContactLog.tyutor_id == tyutor_id,
            ParentContactLog.contact_date.between(start_date, end_date)
        )
    )
    contact_count = result.scalar() or 0
    
    # Har 3 ta aloqa = 5 ball (max 15)
    score = min((contact_count / 3) * 5, 15.0)
    return score


async def calculate_discipline_score(tyutor_id: int, session: AsyncSession) -> float:
    """Intizom (10 ball)"""
    # Tyutor talabalarining statusini tekshirish
    result = await session.execute(
        select(
            func.count(Student.id).filter(Student.status == "active"),
            func.count(Student.id)
        )
        .join(TutorGroup, Student.group_number == TutorGroup.group_number)
        .where(TutorGroup.tutor_id == tyutor_id)
    )
    row = result.one()
    active_count = row[0] or 0
    total_count = row[1] or 0
    
    if total_count == 0:
        return 10.0
    
    # Active talabalar foizi
    active_ratio = active_count / total_count
    score = active_ratio * 10
    return score


async def save_kpi(
    tyutor_id: int, quarter: int, year: int,
    coverage: float, risk: float, activity: float,
    parent: float, discipline: float, total: float,
    session: AsyncSession
):
    """KPI ni bazaga saqlash"""
    # Mavjud KPI ni yangilash yoki yangi yaratish
    result = await session.execute(
        select(TyutorKPI).where(
            TyutorKPI.tyutor_id == tyutor_id,
            TyutorKPI.quarter == quarter,
            TyutorKPI.year == year
        )
    )
    kpi = result.scalar_one_or_none()
    
    if kpi:
        # Yangilash
        kpi.coverage_score = coverage
        kpi.risk_detection_score = risk
        kpi.activity_score = activity
        kpi.parent_contact_score = parent
        kpi.discipline_score = discipline
        kpi.total_kpi = total
        kpi.updated_at = datetime.utcnow()
    else:
        # Yangi yaratish
        kpi = TyutorKPI(
            tyutor_id=tyutor_id,
            quarter=quarter,
            year=year,
            coverage_score=coverage,
            risk_detection_score=risk,
            activity_score=activity,
            parent_contact_score=parent,
            discipline_score=discipline,
            total_kpi=total
        )
        session.add(kpi)
    
    await session.commit()


def get_quarter_dates(quarter: int, year: int) -> tuple[datetime, datetime]:
    """Chorak boshlanish va tugash sanalarini qaytaradi"""
    quarters = {
        1: (datetime(year, 1, 1), datetime(year, 3, 31, 23, 59, 59)),
        2: (datetime(year, 4, 1), datetime(year, 6, 30, 23, 59, 59)),
        3: (datetime(year, 7, 1), datetime(year, 9, 30, 23, 59, 59)),
        4: (datetime(year, 10, 1), datetime(year, 12, 31, 23, 59, 59)),
    }
    return quarters.get(quarter, quarters[1])

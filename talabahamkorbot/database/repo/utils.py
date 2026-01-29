from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import TutorGroup, Student


async def get_tutor_students(session: AsyncSession, tutor_id: int):
    """
    Tyutor biriktirilgan guruhlar bo‘yicha talabalarning ro‘yxatini qaytaradi.
    """
    # Tyutorning guruhlarini olamiz
    groups = await session.execute(
        select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor_id)
    )
    groups = [g[0] for g in groups.all()]

    if not groups:
        return []

    # Shu guruhlardagi talabalarni olamiz
    students = await session.execute(
        select(Student).where(Student.group_number.in_(groups))
    )
    return students.scalars().all()

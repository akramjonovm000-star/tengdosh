
import asyncio
import logging
from sqlalchemy import select
from database.db_connect import AsyncSessionLocal
from database.models import Student, University, Faculty, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def _get_or_create_academic_context(db, uni_name, fac_name=None):
    """Replicated helper for migration script."""
    if not uni_name:
        return None, None
        
    uni = await db.scalar(select(University).where(University.name == uni_name))
    if not uni:
        uni_code = uni_name.replace(" ", "_").upper()[:32]
        uni = University(name=uni_name, uni_code=uni_code)
        db.add(uni)
        await db.flush()
        logger.info(f"Created University: {uni_name}")
    
    uni_id = uni.id
    fac_id = None
    
    if fac_name:
        fac = await db.scalar(select(Faculty).where(Faculty.university_id == uni_id, Faculty.name == fac_name))
        if not fac:
            fac_code = "AUTO_" + fac_name.replace(" ", "_")[:59]
            fac = Faculty(university_id=uni_id, faculty_code=fac_code, name=fac_name)
            db.add(fac)
            await db.flush()
            logger.info(f"Created Faculty: {fac_name} for University {uni_id}")
        fac_id = fac.id
        
    return uni_id, fac_id

async def fix_student_ids():
    async with AsyncSessionLocal() as session:
        # 1. Fix Students
        stmt = select(Student).where(Student.university_id == None)
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        logger.info(f"Found {len(students)} students to fix.")
        
        for student in students:
            if not student.university_name:
                continue
                
            uni_id, fac_id = await _get_or_create_academic_context(session, student.university_name, student.faculty_name)
            student.university_id = uni_id
            student.faculty_id = fac_id
            logger.info(f"Fixed Student {student.id}: Uni={uni_id}, Fac={fac_id}")

        # 2. Fix Users (Shared Auth table)
        stmt_users = select(User).where(User.university_id == None)
        result_users = await session.execute(stmt_users)
        users = result_users.scalars().all()
        
        logger.info(f"Found {len(users)} users to fix.")
        
        for user in users:
            if not user.university_name:
                continue
                
            uni_id, fac_id = await _get_or_create_academic_context(session, user.university_name, user.faculty_name)
            user.university_id = uni_id
            user.faculty_id = fac_id
            logger.info(f"Fixed User {user.id}: Uni={uni_id}, Fac={fac_id}")
            
        await session.commit()
        logger.info("Migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(fix_student_ids())

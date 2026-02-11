
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import University, Faculty

logger = logging.getLogger(__name__)

async def get_or_create_academic_context(db: AsyncSession, uni_name: str, fac_name: str = None):
    """Maps names to IDs, creating records if they don't exist."""
    if not uni_name:
        return None, None
        
    # 1. University
    uni_result = await db.execute(select(University).where(University.name == uni_name))
    uni = uni_result.scalar_one_or_none()
    if not uni:
        # Check for similar names or use a default code
        uni_code = uni_name.replace(" ", "_").upper()[:32]
        uni = University(name=uni_name, uni_code=uni_code)
        db.add(uni)
        await db.flush()
        logger.info(f"Created new University: {uni_name}")
    
    uni_id = uni.id
    fac_id = None
    
    # 2. Faculty
    if fac_name:
        fac_result = await db.execute(select(Faculty).where(Faculty.university_id == uni_id, Faculty.name == fac_name))
        fac = fac_result.scalar_one_or_none()
        if not fac:
            fac_code = "AUTO_" + fac_name.replace(" ", "_")[:59]
            fac = Faculty(university_id=uni_id, faculty_code=fac_code, name=fac_name)
            db.add(fac)
            await db.flush()
            fac_id = fac.id
            logger.info(f"Created new Faculty: {fac_name} for Uni: {uni_id}")
        else:
            fac_id = fac.id
            
    return uni_id, fac_id

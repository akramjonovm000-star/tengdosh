import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup, Student
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def main():
    async with AsyncSessionLocal() as db:
        # Check Maxmanazarov
        tutor_id = 74
        groups_result2 = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor_id))
        group_numbers = groups_result2.scalars().all()
        print(f"Groups: {group_numbers}")
        
        # Test Hemingway
        hemis_student_count = await HemisService.get_total_students_for_groups(group_numbers, HEMIS_ADMIN_TOKEN)
        print(f"Hemis count: {hemis_student_count}")
        
        # Test Active count
        active_student_count = await db.scalar(
            select(func.count(Student.id))
            .where(
                Student.group_number.in_(group_numbers),
                Student.hemis_token.is_not(None) # Fixed syntax to proper is_not() earlier or != None
            )
        )
        print(f"Active count: {active_student_count}")
        
if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())

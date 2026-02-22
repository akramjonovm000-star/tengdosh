import asyncio
from sqlalchemy import select, func
from database.db_connect import AsyncSessionLocal
from database.models import Staff, TutorGroup, Student

async def main():
    async with AsyncSessionLocal() as db:
        # Check Maxmanazarov
        tutor_id = 74
        groups_result = await db.execute(select(TutorGroup.group_number).where(TutorGroup.tutor_id == tutor_id))
        group_numbers = groups_result.scalars().all()
        print(f"Groups length: {len(group_numbers)}")
        
        # Test Active count with hemis_token != None
        active_student_count = await db.scalar(
            select(func.count(Student.id))
            .where(
                Student.group_number.in_(group_numbers),
                Student.hemis_token != None
            )
        )
        print(f"Active count (hemis_token != None): {active_student_count}")
        
        # Look for any student with hemis_token in the DB
        total_tokens = await db.scalar(
            select(func.count(Student.id)).where(Student.hemis_token != None)
        )
        print(f"Total students with hemis_token in entire DB: {total_tokens}")

        # Look for any student with updated_at != created_at maybe?
        
if __name__ == "__main__":
    import sys
    sys.path.append("/home/user/talabahamkor/talabahamkorbot")
    asyncio.run(main())
